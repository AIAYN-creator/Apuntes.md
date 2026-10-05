<#
.SYNOPSIS
  Enlaza las skills del repo (apuntes-a-md y enlazar-apuntes) en los agentes elegidos
  (junction: los cambios del repo se ven al instante).

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

$skills = @('apuntes-a-md', 'enlazar-apuntes') | ForEach-Object {
  $ruta = Join-Path $PSScriptRoot "skills\$_"
  if (-not (Test-Path (Join-Path $ruta 'SKILL.md'))) { throw "No encuentro $ruta\SKILL.md" }
  [pscustomobject]@{ Nombre = $_; Ruta = $ruta }
}

$destinos = @{
  claude = Join-Path $HOME '.claude\skills'
  gemini = Join-Path $HOME '.gemini\skills'
  codex  = Join-Path $HOME '.codex\skills'
  agents = Join-Path $HOME '.agents\skills'
}

foreach ($a in $Agentes) {
  foreach ($s in $skills) {
    $enlace = Join-Path $destinos[$a] $s.Nombre
    if (Test-Path $enlace) {
      $item = Get-Item $enlace -Force
      if ($item.LinkType -eq 'Junction' -and ((@($item.Target)[0]).TrimEnd('\') -eq $s.Ruta.TrimEnd('\'))) {
        Write-Host "[$a] $($s.Nombre) ya instalada: $enlace"
      } else {
        Write-Warning "[$a] $enlace ya existe y no apunta a este repo; no lo toco."
      }
      continue
    }
    if ($PSCmdlet.ShouldProcess($enlace, "crear junction -> $($s.Ruta)")) {
      New-Item -ItemType Directory -Force $destinos[$a] | Out-Null
      New-Item -ItemType Junction -Path $enlace -Target $s.Ruta | Out-Null
      Write-Host "[$a] $($s.Nombre) instalada: $enlace -> $($s.Ruta)"
    }
  }
}
