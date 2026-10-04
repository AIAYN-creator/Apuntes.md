<#
.SYNOPSIS
  Enlaza la skill apuntes-a-md en los agentes elegidos (junction: los cambios del repo se ven al instante).

.EXAMPLE
  .\instalar.ps1                          # solo Claude Code
  .\instalar.ps1 -Agentes claude,gemini,codex
  .\instalar.ps1 -Agentes gemini -WhatIf  # muestra lo que haría, sin tocar nada

.NOTES
  Carpetas de skills de cada agente (formato abierto Agent Skills, SKILL.md):
    claude -> ~/.claude/skills    gemini -> ~/.gemini/skills
    codex  -> ~/.codex/skills     agents -> ~/.agents/skills  (alias compartido, p. ej. Gemini CLI)
#>
[CmdletBinding(SupportsShouldProcess)]
param(
  [ValidateSet('claude', 'gemini', 'codex', 'agents')]
  [string[]]$Agentes = @('claude')
)

$skill = Join-Path $PSScriptRoot 'skills\apuntes-a-md'
if (-not (Test-Path (Join-Path $skill 'SKILL.md'))) { throw "No encuentro $skill\SKILL.md" }

$destinos = @{
  claude = Join-Path $HOME '.claude\skills'
  gemini = Join-Path $HOME '.gemini\skills'
  codex  = Join-Path $HOME '.codex\skills'
  agents = Join-Path $HOME '.agents\skills'
}

foreach ($a in $Agentes) {
  $enlace = Join-Path $destinos[$a] 'apuntes-a-md'
  if (Test-Path $enlace) {
    $item = Get-Item $enlace -Force
    if ($item.LinkType -eq 'Junction' -and ((@($item.Target)[0]).TrimEnd('\') -eq $skill.TrimEnd('\'))) {
      Write-Host "[$a] ya instalada: $enlace"
    } else {
      Write-Warning "[$a] $enlace ya existe y no apunta a este repo; no lo toco."
    }
    continue
  }
  if ($PSCmdlet.ShouldProcess($enlace, "crear junction -> $skill")) {
    New-Item -ItemType Directory -Force $destinos[$a] | Out-Null
    New-Item -ItemType Junction -Path $enlace -Target $skill | Out-Null
    Write-Host "[$a] instalada: $enlace -> $skill"
  }
}
