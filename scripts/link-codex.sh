#!/usr/bin/env bash
set -euo pipefail

# 将本仓库的 Codex 工作流部署到目标项目。第一个参数优先于 TARGET_PATH。
# 示例：
#   ./scripts/link-codex.sh /path/to/target-project
#   TARGET_PATH=/path/to/target-project ./scripts/link-codex.sh
#   FORCE=1 ./scripts/link-codex.sh /path/to/target-project
#
# Codex 仅从 $CODEX_HOME/prompts/ 发现自定义 prompts，因此命令会链接到
# 该用户级目录；agents、skills、规则和项目配置仍部署在目标项目中。
TARGET_PATH="${1:-${TARGET_PATH:-}}"
FORCE="${FORCE:-0}"
CODEX_HOME="${CODEX_HOME:-${HOME}/.codex}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_CODEX_DIR="${SOURCE_ROOT}/.codex"
SOURCE_SKILLS_DIR="${SOURCE_ROOT}/.agents/skills"

if [[ -z "${TARGET_PATH}" ]]; then
  cat >&2 <<'EOF'
请提供目标项目根目录：
  ./scripts/link-codex.sh /path/to/target-project
  TARGET_PATH=/path/to/target-project ./scripts/link-codex.sh

可选环境变量：
  FORCE=1      备份并替换冲突的目标文件或目录。
  CODEX_HOME=  Codex 用户目录，默认是 ~/.codex。
EOF
  exit 1
fi

for required_path in \
  "${SOURCE_ROOT}/AGENTS.md" \
  "${SOURCE_CODEX_DIR}/agents" \
  "${SOURCE_CODEX_DIR}/demand-workflow" \
  "${SOURCE_CODEX_DIR}/prompts" \
  "${SOURCE_CODEX_DIR}/rules" \
  "${SOURCE_CODEX_DIR}/config.toml" \
  "${SOURCE_SKILLS_DIR}"; do
  if [[ ! -e "${required_path}" ]]; then
    echo "缺少 Codex 源文件：${required_path}" >&2
    exit 1
  fi
done

mkdir -p "${TARGET_PATH}"
TARGET_ROOT="$(cd "${TARGET_PATH}" && pwd)"
mkdir -p "${CODEX_HOME}"
CODEX_HOME="$(cd "${CODEX_HOME}" && pwd)"

backup_existing() {
  local target_path="$1"
  local timestamp
  timestamp="$(date +%Y%m%d%H%M%S)"
  local backup_path="${target_path}.codex-backup-${timestamp}"
  local sequence=1

  while [[ -e "${backup_path}" || -L "${backup_path}" ]]; do
    backup_path="${target_path}.codex-backup-${timestamp}-${sequence}"
    sequence=$((sequence + 1))
  done

  mv "${target_path}" "${backup_path}"
  echo "已备份冲突项：${target_path} -> ${backup_path}"
}

link_entry() {
  local source_path="$1"
  local target_path="$2"

  if [[ "${source_path}" == "${target_path}" ]]; then
    echo "源路径与目标路径相同，跳过：${target_path}"
    return
  fi

  mkdir -p "$(dirname "${target_path}")"

  if [[ -L "${target_path}" ]]; then
    local current_target
    current_target="$(readlink "${target_path}")"
    if [[ "${current_target}" == "${source_path}" ]]; then
      echo "链接已存在，跳过：${target_path} -> ${source_path}"
      return
    fi

    if [[ "${FORCE}" != "1" ]]; then
      echo "目标链接已存在但指向不同位置：${target_path} -> ${current_target}" >&2
      echo "如需替换并保留备份，请设置 FORCE=1。" >&2
      return 1
    fi
    backup_existing "${target_path}"
  elif [[ -e "${target_path}" ]]; then
    if [[ "${FORCE}" != "1" ]]; then
      echo "目标已存在：${target_path}" >&2
      echo "如需替换并保留备份，请设置 FORCE=1。" >&2
      return 1
    fi
    backup_existing "${target_path}"
  fi

  ln -s "${source_path}" "${target_path}"
  echo "已创建链接：${target_path} -> ${source_path}"
}

link_entry "${SOURCE_ROOT}/AGENTS.md" "${TARGET_ROOT}/AGENTS.md"
link_entry "${SOURCE_CODEX_DIR}/config.toml" "${TARGET_ROOT}/.codex/config.toml"

for source_path in "${SOURCE_CODEX_DIR}/agents/"*.toml; do
  [[ -f "${source_path}" ]] || continue
  link_entry "${source_path}" "${TARGET_ROOT}/.codex/agents/$(basename "${source_path}")"
done

for source_path in "${SOURCE_CODEX_DIR}/demand-workflow/"*.json; do
  [[ -f "${source_path}" ]] || continue
  link_entry "${source_path}" "${TARGET_ROOT}/.codex/demand-workflow/$(basename "${source_path}")"
done

for source_path in "${SOURCE_CODEX_DIR}/rules/"*.rules; do
  [[ -f "${source_path}" ]] || continue
  link_entry "${source_path}" "${TARGET_ROOT}/.codex/rules/$(basename "${source_path}")"
done

for source_path in "${SOURCE_SKILLS_DIR}/"*; do
  [[ -d "${source_path}" ]] || continue
  link_entry "${source_path}" "${TARGET_ROOT}/.agents/skills/$(basename "${source_path}")"
done

for source_path in "${SOURCE_CODEX_DIR}/prompts/"*.md; do
  [[ -f "${source_path}" ]] || continue
  link_entry "${source_path}" "${CODEX_HOME}/prompts/$(basename "${source_path}")"
done

cat <<EOF
完成。请在目标项目根目录启动 Codex，并确保项目被标记为 trusted。

已部署：
- ${TARGET_ROOT}/AGENTS.md
- ${TARGET_ROOT}/.codex/{config.toml,agents,demand-workflow,rules}
- ${TARGET_ROOT}/.agents/skills
- ${CODEX_HOME}/prompts/techbot-start.md
- ${CODEX_HOME}/prompts/techbot-bug-fix.md

重启 Codex 或新建会话后，可使用：
- /prompts:techbot-start <需求描述>
- /prompts:techbot-bug-fix <Bug 描述>
EOF
