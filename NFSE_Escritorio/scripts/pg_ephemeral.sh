#!/usr/bin/env bash
# PostgreSQL EFÊMERO para testes locais (socket unix, sem rede, sem cloud).
# Uso: scripts/pg_ephemeral.sh start   -> imprime TEST_DATABASE_URL
#      scripts/pg_ephemeral.sh stop
# Diretório: PG_EPHEMERAL_DIR (padrão /tmp/nfse-pg-test). Só aceita caminho canônico
# diretamente em /tmp com nome nfse-pg-test[-sufixo]; diretório preexistente sem o marcador
# de ownership é recusado. Nunca edita /etc/passwd ou /etc/group: como root, usa o usuário
# não privilegiado existente PG_EPHEMERAL_USER (padrão nobody) ou falha.
set -euo pipefail
RAW=${PG_EPHEMERAL_DIR:-/tmp/nfse-pg-test}
PORT=${PG_EPHEMERAL_PORT:-54329}
MARK=.nfse-pg-test-owner
die() { echo "pg_ephemeral: $*" >&2; exit 2; }

case "$RAW" in /*) ;; *) die "caminho precisa ser absoluto";; esac
DIR=$(realpath -m -- "$RAW")
[ "$DIR" = "$RAW" ] || [ "$DIR/" = "$RAW" ] || die "caminho não canônico: $RAW"
[ "$(dirname -- "$DIR")" = /tmp ] || die "fora da área dedicada /tmp: $DIR"
case "$(basename -- "$DIR")" in
  nfse-pg-test|nfse-pg-test-[A-Za-z0-9_]*) ;;
  *) die "nome precisa ser nfse-pg-test[-sufixo]: $DIR";;
esac
[ -L "$RAW" ] && die "symlink recusado: $RAW"
[ "${PG_EPHEMERAL_GUARD_ONLY:-}" = 1 ] && { echo "guard ok: $DIR"; exit 0; }

owned() { [ -d "$DIR" ] && [ ! -L "$DIR" ] && [ -f "$DIR/$MARK" ] && [ "$(cat "$DIR/$MARK")" = "nfse-pg-test $DIR" ]; }
wipe() { owned || die "recusado apagar $DIR sem marcador de ownership"; rm -rf -- "$DIR"; }

case "${1:-}" in
  start) if [ -e "$DIR" ] || [ -L "$DIR" ]; then owned || die "$DIR já existe sem marcador de ownership; recusado"; fi ;;
  stop) owned || die "$DIR sem marcador de ownership; nada feito" ;;
esac

if [ "$(id -u)" = 0 ]; then
  U=${PG_EPHEMERAL_USER:-nobody}
  getent passwd "$U" >/dev/null || die "usuário não privilegiado '$U' inexistente; defina PG_EPHEMERAL_USER"
  UID_=$(id -u "$U"); GID_=$(id -g "$U")
  [ "$UID_" != 0 ] || die "usuário '$U' é privilegiado"
  run() { setpriv --reuid="$UID_" --regid="$GID_" --clear-groups env HOME=/tmp "$@"; }
else
  run() { "$@"; }
fi
DATA="$DIR/data"

case "${1:-}" in
  start)
    if [ -e "$DIR" ] || [ -L "$DIR" ]; then
      owned || die "$DIR já existe sem marcador de ownership; recusado"
      run pg_ctl -D "$DATA" status >/dev/null 2>&1 && run pg_ctl -D "$DATA" stop -m fast >/dev/null || true
      wipe
    fi
    mkdir -m 711 -- "$DIR"; printf 'nfse-pg-test %s' "$DIR" > "$DIR/$MARK"
    mkdir -m 700 -- "$DATA"
    [ "$(id -u)" = 0 ] && chown "$UID_:$GID_" "$DATA"
    run initdb -D "$DATA" -U postgres -A trust -E UTF8 --locale=C >/dev/null
    run pg_ctl -D "$DATA" -o "-p $PORT -k /tmp -c listen_addresses=''" -l "$DATA/pg.log" -w start >/dev/null
    psql -h /tmp -p "$PORT" -U postgres -qc "CREATE DATABASE nfse_test" >/dev/null
    echo "postgresql://postgres@/nfse_test?host=/tmp&port=$PORT"
    ;;
  stop)
    owned || die "$DIR sem marcador de ownership; nada feito"
    run pg_ctl -D "$DATA" stop -m fast >/dev/null || true
    wipe; echo stopped
    ;;
  *) echo "uso: $0 start|stop" >&2; exit 64 ;;
esac
