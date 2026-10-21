# Confere o que o pipeline precisa neste computador. Nao instala nada.
# Uso (na pasta pipeline-criaturas):
#   powershell -ExecutionPolicy Bypass -File scripts\verificar-ambiente.ps1

$falta = New-Object System.Collections.Generic.List[string]

function Ok($msg) { Write-Host "[ok]    $msg" -ForegroundColor Green }
function Aviso($msg) { Write-Host "[aviso] $msg" -ForegroundColor Cyan }
function Falta($msg, $cmd) {
    Write-Host "[falta] $msg" -ForegroundColor Yellow
    if ($cmd) { Write-Host "        $cmd"; $script:falta.Add($cmd) }
}
function Tem($exe) { return [bool](Get-Command $exe -ErrorAction SilentlyContinue) }

# Git e identidade dos commits
if (Tem "git") {
    Ok ("Git " + ((git --version) -replace 'git version ', ''))
    $nome = git config --global user.name
    $email = git config --global user.email
    if ($nome -and $email) { Ok "identidade do Git: $nome <$email>" }
    else { Falta "identidade do Git (nome e e-mail que aparecem nos commits)" 'git config --global user.name "Seu Nome"; git config --global user.email "seu-email"' }
} else { Falta "Git for Windows" "winget install --id Git.Git -e" }

# GitHub CLI e login
if (Tem "gh") {
    Ok "GitHub CLI"
    gh auth status *> $null
    if ($LASTEXITCODE -eq 0) { Ok "login no GitHub" } else { Falta "login no GitHub" "gh auth login" }
} else { Falta "GitHub CLI" "winget install --id GitHub.cli -e" }

# Node.js 23.6 ou mais novo (o render headless precisa)
if (Tem "node") {
    $v = (node --version).TrimStart('v')
    $p = $v.Split('.')
    $maj = [int]$p[0]; $min = [int]$p[1]
    if ($maj -gt 23 -or ($maj -eq 23 -and $min -ge 6)) { Ok "Node.js $v" }
    else { Falta "Node.js $v e antigo (precisa 23.6 ou mais novo)" "winget upgrade --id OpenJS.NodeJS.LTS -e   (ou instale o Node LTS de nodejs.org)" }
} else { Falta "Node.js" "winget install --id OpenJS.NodeJS.LTS -e" }

# uv (Python)
if (Tem "uv") { Ok ("uv " + ((uv --version) -replace 'uv ', '')) }
else { Falta "uv (gerenciador de Python)" "winget install --id astral-sh.uv -e" }

# Claude Code
if (Tem "claude") {
    $cv = (claude --version) 2>$null
    Ok "Claude Code $cv"
    if ("$cv" -match '(\d+)\.(\d+)\.(\d+)') {
        $a = [int]$Matches[1]; $b = [int]$Matches[2]; $c = [int]$Matches[3]
        if ($a -lt 2 -or ($a -eq 2 -and ($b -lt 1 -or ($b -eq 1 -and $c -lt 283)))) {
            Aviso "Claude Code anterior a 2.1.283: rode  claude update"
        }
    }
} else { Falta "Claude Code" "irm https://claude.ai/install.ps1 | iex" }

# Blockbench
$bb = @("$env:LOCALAPPDATA\Programs\Blockbench\Blockbench.exe", "$env:ProgramFiles\Blockbench\Blockbench.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if ($bb) { Ok "Blockbench ($bb)" }
else { Falta "Blockbench (nao achei nas pastas padrao)" "winget install --id JannisX11.Blockbench -e" }

# Obsidian
$ob = @("$env:LOCALAPPDATA\Programs\Obsidian\Obsidian.exe", "$env:LOCALAPPDATA\Obsidian\Obsidian.exe", "$env:ProgramFiles\Obsidian\Obsidian.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if ($ob) { Ok "Obsidian" }
else { Falta "Obsidian (nao achei nas pastas padrao)" "winget install --id Obsidian.Obsidian -e" }

# Plugin MCP do Blockbench (so responde com o app aberto e o plugin carregado)
try {
    Invoke-WebRequest -Uri "http://localhost:3000/bb-mcp" -Method Get -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop | Out-Null
    Ok "servidor MCP do Blockbench respondendo"
} catch {
    if ($_.Exception.Response) { Ok "servidor MCP do Blockbench respondendo" }
    else { Aviso "servidor MCP do Blockbench nao respondeu (normal se o Blockbench estiver fechado ou sem o plugin)" }
}

# Pasta certa?
if (Test-Path ".mcp.json") { Ok "rodando na pasta do kit" }
else { Aviso "rode este script dentro da pasta pipeline-criaturas" }

Write-Host ""
if ($falta.Count -eq 0) {
    Write-Host "Tudo pronto. Abra o Claude Code nesta pasta:  claude --permission-mode auto" -ForegroundColor Green
} else {
    Write-Host "Falta(m) $($falta.Count) item(ns). Rode os comandos acima, feche e abra o terminal e rode este script de novo." -ForegroundColor Yellow
}
