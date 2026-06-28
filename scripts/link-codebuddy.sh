#!/usr/bin/env bash
set -euo pipefail

# 目标项目根目录。可直接修改这里，或执行时传入第一个参数覆盖。
# 示例：TARGET_PATH="/path/to/target-project"
TARGET_PATH="${1:-${TARGET_PATH:-}}"

# 设置为 1 时，会替换目标目录下已存在的同名文件/目录/链接。
FORCE="${FORCE:-0}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_CODEBUDDY_DIR="${PROJECT_ROOT}/.codebuddy"

if [[ -z "${TARGET_PATH}" ]]; then
  echo "请在脚本中设置 TARGET_PATH，或执行时传入目标项目根目录："
  echo "  TARGET_PATH=/path/to/target-project $0"
  echo "  $0 /path/to/target-project"
  exit 1
fi

if [[ ! -d "${SOURCE_CODEBUDDY_DIR}" ]]; then
  echo "源目录不存在：${SOURCE_CODEBUDDY_DIR}"
  exit 1
fi

mkdir -p "${TARGET_PATH}"
TARGET_PATH="$(cd "${TARGET_PATH}" && pwd)"
TARGET_CODEBUDDY_DIR="${TARGET_PATH}/.codebuddy"
mkdir -p "${TARGET_CODEBUDDY_DIR}"

link_entry() {
  local source_path="$1"
  local target_path="$2"

  if [[ -L "${target_path}" ]]; then
    local current_target
    current_target="$(readlink "${target_path}")"
    if [[ "${current_target}" == "${source_path}" ]]; then
      echo "已存在链接，跳过：${target_path} -> ${source_path}"
      return
    fi

    if [[ "${FORCE}" == "1" ]]; then
      rm "${target_path}"
    else
      echo "目标链接已存在但指向不同位置，跳过：${target_path} -> ${current_target}"
      return
    fi
  elif [[ -e "${target_path}" ]]; then
    if [[ "${FORCE}" == "1" ]]; then
      rm -rf "${target_path}"
    else
      echo "目标已存在，跳过：${target_path}。如需覆盖，请设置 FORCE=1。"
      return
    fi
  fi

  ln -s "${source_path}" "${target_path}"
  echo "已创建链接：${target_path} -> ${source_path}"
}

for source_entry in "${SOURCE_CODEBUDDY_DIR}"/*; do
  [[ -e "${source_entry}" ]] || continue
  entry_name="$(basename "${source_entry}")"
  link_entry "${source_entry}" "${TARGET_CODEBUDDY_DIR}/${entry_name}"
done

echo "完成：${SOURCE_CODEBUDDY_DIR} 的内容已通过软链接同步到 ${TARGET_CODEBUDDY_DIR}"
