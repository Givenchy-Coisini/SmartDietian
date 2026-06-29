#!/usr/bin/env node
/**
 * scripts/git-commit-push.cjs
 *
 * Node.js 版本的一键 commit + push 脚本，与 git-commit-push.ps1 行为完全一致。
 * 选用 .cjs 后缀以兼容前端项目（frontend/package.json 的 "type": "module" 不会影响这个文件）。
 *
 * 用法：
 *   node scripts/git-commit-push.cjs "提交信息"
 *   node scripts/git-commit-push.cjs "提交信息" --path app frontend/src/utils
 *   node scripts/git-commit-push.cjs "提交信息" --no-push
 *   node scripts/git-commit-push.cjs "提交信息" --branch dev --remote origin
 *   node scripts/git-commit-push.cjs "提交信息" --retries 5 --retry-delay 3
 *   node scripts/git-commit-push.cjs -h
 *
 * 沉淀的踩坑经验：
 *   1. commit message 以 UTF-8 无 BOM 临时文件 + git commit -F 写入，避免控制台编码问题。
 *   2. push 失败默认重试 3 次、间隔 5 秒。
 *   3. add 默认 -A，可用 --path 精确指定路径。
 */

'use strict'

const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const crypto = require('node:crypto')
const { spawnSync } = require('node:child_process')

// 备注：在 Windows + PowerShell 5 控制台下，本脚本的中文日志可能显示乱码，
// 这是 PowerShell 控制台默认 OEM 代码页（GBK）解码 UTF-8 字节导致的显示问题，
// 不影响 git 仓库实际存储的字节（仍是正确的 UTF-8）。如想正常显示，请在 PowerShell 中执行：
//   [Console]::OutputEncoding = [Text.Encoding]::UTF8
//   chcp 65001
// 或永久写入 PowerShell profile。

const COLORS = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m'
}
const useColor = process.stdout.isTTY && !process.env.NO_COLOR
const c = (color, text) => (useColor ? `${COLORS[color]}${text}${COLORS.reset}` : text)
const log = {
  info: (m) => console.log(c('cyan', '[INFO] ') + m),
  ok: (m) => console.log(c('green', '[OK]   ') + m),
  warn: (m) => console.log(c('yellow', '[WARN] ') + m),
  error: (m) => console.error(c('red', '[ERROR] ') + m)
}

function showHelp() {
  const help = `
git-commit-push.cjs  —  一键 commit + push（带 3 次重试、UTF-8 无 BOM 提交信息）

用法：
  node scripts/git-commit-push.cjs <message> [options]

选项：
  --path <p...>          指定要 git add 的路径（默认 git add -A）
  --remote <name>        远端名（默认 origin）
  --branch <name>        分支名（默认当前分支）
  --retries <n>          push 失败重试次数（默认 3）
  --retry-delay <sec>    push 重试间隔秒数（默认 5）
  --no-push              只 commit 不 push
  --allow-empty          允许创建空 commit
  -h, --help             查看帮助

示例：
  node scripts/git-commit-push.cjs "提交信息"
  node scripts/git-commit-push.cjs "提交信息" --path app frontend/src
  node scripts/git-commit-push.cjs "提交信息" --no-push
`.trim()
  console.log(help)
}

function parseArgs(argv) {
  const args = {
    message: '',
    paths: [],
    remote: 'origin',
    branch: '',
    retries: 3,
    retryDelay: 5,
    noPush: false,
    allowEmpty: false,
    help: false
  }
  const positional = []
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '-h' || a === '--help') {
      args.help = true
    } else if (a === '--no-push') {
      args.noPush = true
    } else if (a === '--allow-empty') {
      args.allowEmpty = true
    } else if (a === '--remote') {
      args.remote = argv[++i]
    } else if (a === '--branch') {
      args.branch = argv[++i]
    } else if (a === '--retries') {
      args.retries = parseInt(argv[++i], 10)
    } else if (a === '--retry-delay') {
      args.retryDelay = parseInt(argv[++i], 10)
    } else if (a === '--path') {
      // 吃掉后续所有非 -- 开头的参数作为路径
      while (i + 1 < argv.length && !argv[i + 1].startsWith('-')) {
        args.paths.push(argv[++i])
      }
    } else if (a.startsWith('--')) {
      log.error(`未知参数: ${a}`)
      process.exit(1)
    } else {
      positional.push(a)
    }
  }
  if (positional.length > 0) {
    args.message = positional.join(' ')
  }
  return args
}

function runGit(gitArgs, opts = {}) {
  // 关键：Windows 下 git 输出是 UTF-8 字节，但 Node 默认会按 OEM 代码页（GBK）解码，
  // 导致中文路径变乱码。这里用 buffer 模式抓字节，再手动按 UTF-8 解码。
  const result = spawnSync('git', gitArgs, {
    stdio: opts.capture ? ['ignore', 'pipe', 'pipe'] : 'inherit',
    shell: false
  })
  if (result.error) {
    log.error(`无法执行 git: ${result.error.message}`)
    process.exit(1)
  }
  const decode = (buf) => (Buffer.isBuffer(buf) ? buf.toString('utf8') : String(buf ?? ''))
  return {
    code: result.status ?? -1,
    stdout: decode(result.stdout).trim(),
    stderr: decode(result.stderr).trim()
  }
}

async function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

async function main() {
  const args = parseArgs(process.argv.slice(2))

  if (args.help) {
    showHelp()
    return 0
  }
  if (!args.message || !args.message.trim()) {
    showHelp()
    console.log('')
    log.error('必须提供 commit message。')
    return 1
  }

  // 1. 确认是 git 仓库
  const repo = runGit(['rev-parse', '--show-toplevel'], { capture: true })
  if (repo.code !== 0 || !repo.stdout) {
    log.error('当前目录不是一个 git 仓库。')
    return 1
  }
  const repoRoot = repo.stdout
  process.chdir(repoRoot)
  log.info(`仓库根目录: ${repoRoot}`)

  // 2. 确定分支
  let branch = args.branch
  if (!branch) {
    const r = runGit(['rev-parse', '--abbrev-ref', 'HEAD'], { capture: true })
    branch = r.stdout
    if (r.code !== 0 || !branch || branch === 'HEAD') {
      log.error('无法确定当前分支（detached HEAD？）。请用 --branch 显式指定。')
      return 1
    }
  }
  log.info(`目标分支: ${branch}    远端: ${args.remote}`)

  // 3. git add
  if (args.paths.length > 0) {
    log.info(`git add 指定路径: ${args.paths.join(', ')}`)
    const r = runGit(['add', '--', ...args.paths])
    if (r.code !== 0) {
      log.error('git add 失败。')
      return 1
    }
  } else {
    log.info('git add -A（全部变更）')
    const r = runGit(['add', '-A'])
    if (r.code !== 0) {
      log.error('git add 失败。')
      return 1
    }
  }

  // 4. 检查暂存区
  const diff = runGit(['diff', '--cached', '--quiet'], { capture: true })
  const hasStaged = diff.code !== 0
  if (!hasStaged && !args.allowEmpty) {
    log.warn('暂存区没有任何改动，跳过 commit。')
    log.warn('如果你想创建空 commit，加 --allow-empty 参数。')
    if (args.noPush) return 0
    log.info('仍尝试 push（同步现有 commit）...')
  } else {
    // 5. 写 UTF-8 无 BOM 临时文件
    const tmpName = 'COMMIT_MSG_TMP_' + crypto.randomBytes(4).toString('hex') + '.txt'
    const tmpFile = path.join(repoRoot, tmpName)
    try {
      fs.writeFileSync(tmpFile, args.message, { encoding: 'utf8' })
      // 6. commit
      const commitArgs = ['commit', '-F', tmpFile]
      if (args.allowEmpty) commitArgs.push('--allow-empty')
      const r = runGit(commitArgs)
      if (r.code !== 0) {
        log.error('git commit 失败。')
        return 1
      }
      const hash = runGit(['rev-parse', '--short', 'HEAD'], { capture: true }).stdout
      log.ok(`commit ${hash} 已生成。`)
    } finally {
      try { fs.unlinkSync(tmpFile) } catch (_) { /* ignore */ }
    }
  }

  // 7. push
  if (args.noPush) {
    log.info('--no-push 指定，跳过推送。')
    return 0
  }

  for (let attempt = 1; attempt <= args.retries; attempt++) {
    log.info(`git push ${args.remote} ${branch}  (第 ${attempt}/${args.retries} 次尝试)`)
    const r = runGit(['push', args.remote, branch])
    if (r.code === 0) {
      log.ok(`push 成功 -> ${args.remote}/${branch}`)
      return 0
    }
    log.warn(`第 ${attempt} 次推送失败（exit=${r.code}）`)
    if (attempt < args.retries) {
      log.warn(`${args.retryDelay} 秒后重试...`)
      await sleep(args.retryDelay * 1000)
    }
  }

  log.error(`${args.retries} 次推送都失败了。你可以手动重试：git push ${args.remote} ${branch}`)
  return 1
}

main().then((code) => process.exit(code)).catch((err) => {
  log.error(`未捕获异常: ${err && err.stack ? err.stack : err}`)
  process.exit(1)
})
