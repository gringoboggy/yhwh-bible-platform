# Shared helpers for reader_sim/*.sh — source from sibling scripts.
reader_sim_repo() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

reader_sim_py() {
  if command -v py >/dev/null 2>&1; then
    echo "py -3"
  else
    echo "python3"
  fi
}