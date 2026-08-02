<#
.SYNOPSIS
    Resume an interrupted transcription batch automatically after a reboot.

.DESCRIPTION
    Registers a Scheduled Task that re-runs _transcribe_batch.py at logon.
    The batch is resumable -- a recording whose .txt already exists is skipped --
    so re-running it costs nothing and picks up exactly where it stopped.

    Written for a machine that hard-resets without warning: 10 unexpected
    restarts in 95 days, all Kernel-Power Event 41 with BugcheckCode 0. See
    "Unresolved: the machine hard-reboots" in TRANSCRIPTION-PROGRAM.md. This
    script does not fix that fault. It makes multi-hour runs survive it.

    Logs every start, exit and skip to a journal beside the output directory,
    which doubles as a record of when the machine died and what it was doing.

.PARAMETER Install
    Register the scheduled task, then exit. Does not start a run.

.PARAMETER Uninstall
    Remove the scheduled task.

.PARAMETER Status
    Show the task state and the tail of the journal.

.PARAMETER Run
    Execute a resume pass. This is what the scheduled task invokes; you rarely
    want it by hand.

.PARAMETER PollMinutes
    How often the safety-net trigger re-checks, in minutes (default 15). A
    logon trigger alone is not enough: it fires on a logon EVENT, so a reset
    with nobody present to log in leaves the batch stopped. Firing often is
    cheap -- the run refuses to start beside a live batch and exits at once
    when there is nothing to do.

.PARAMETER KeepEnabled
    Do not disable the task once the corpus is complete. By default a run that
    finds nothing left to do disables the task, so a finished job does not leave
    something firing at every logon for months.

.EXAMPLE
    # one-time setup
    .\Scripts\_transcribe_autoresume.ps1 -Install `
        -Manifest E:\MD-Transcription\manifest-tier1.tsv `
        -Audio    E:\MD-Transcription\audio `
        -Out      E:\MD-Transcription\transcripts-gpu-mc0 -Workers 1

.EXAMPLE
    .\Scripts\_transcribe_autoresume.ps1 -Status

.NOTES
    Triggers at LOGON, not at STARTUP, and deliberately. A task running as
    SYSTEM in session 0 before anyone logs in generally cannot enumerate the
    GPU, so a Vulkan build fails there. If the machine does not log in
    automatically, the resume waits for a login -- which is the correct
    behaviour anyway on a box whose resets are not understood.
#>
[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Install', Mandatory = $true)][switch]$Install,
    [Parameter(ParameterSetName = 'Uninstall', Mandatory = $true)][switch]$Uninstall,
    [Parameter(ParameterSetName = 'Status')][switch]$Status,
    [Parameter(ParameterSetName = 'Run', Mandatory = $true)][switch]$Run,

    [Parameter(ParameterSetName = 'Install', Mandatory = $true)]
    [Parameter(ParameterSetName = 'Run', Mandatory = $true)][string]$Manifest,

    [Parameter(ParameterSetName = 'Install', Mandatory = $true)]
    [Parameter(ParameterSetName = 'Run', Mandatory = $true)][string]$Audio,

    [Parameter(ParameterSetName = 'Install', Mandatory = $true)]
    [Parameter(ParameterSetName = 'Run', Mandatory = $true)][string]$Out,

    [Parameter(ParameterSetName = 'Install')]
    [Parameter(ParameterSetName = 'Run')][int]$Workers = 1,

    [Parameter(ParameterSetName = 'Run')][string]$Python = 'python',

    [Parameter(ParameterSetName = 'Install')][int]$DelayMinutes = 3,
    [Parameter(ParameterSetName = 'Install')][int]$PollMinutes = 15,
    [Parameter(ParameterSetName = 'Run')][switch]$KeepEnabled
)

$ErrorActionPreference = 'Stop'
$TaskName = 'MD-Transcribe-Resume'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BatchPy = Join-Path $PSScriptRoot '_transcribe_batch.py'

function Get-Journal {
    param([string]$OutDir)
    Join-Path (Split-Path -Parent $OutDir) 'autoresume-journal.log'
}

function Write-Journal {
    param([string]$Path, [string]$Message)
    $line = "{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Add-Content -Path $Path -Value $line -Encoding utf8
    Write-Host $line
}

# ---------------------------------------------------------------- install ----
if ($Install) {
    foreach ($p in @($Manifest, $Audio)) {
        if (-not (Test-Path $p)) { throw "not found: $p" }
    }
    if (-not (Test-Path $Out)) { New-Item -ItemType Directory -Path $Out -Force | Out-Null }

    # Pin the interpreter. A scheduled task inheriting a different PATH than the
    # shell you installed from would fail silently at 3am, which is the one time
    # nobody is watching. Note for the cpu backend: Anaconda's MKL OpenMP
    # collides with CTranslate2 and costs ~10x -- irrelevant here, since the gpu
    # backend only uses python to orchestrate whisper-cli and convert WAVs.
    $py = (Get-Command python -EA SilentlyContinue).Source
    if (-not $py) { throw "python not found on PATH; cannot pin an interpreter for the task" }
    Write-Host "pinned interpreter: $py"

    $argline = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden',
        '-File', ('"{0}"' -f $PSCommandPath), '-Run',
        '-Python', ('"{0}"' -f $py),
        '-Manifest', ('"{0}"' -f $Manifest),
        '-Audio', ('"{0}"' -f $Audio),
        '-Out', ('"{0}"' -f $Out),
        '-Workers', $Workers
    ) -join ' '

    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $argline `
        -WorkingDirectory $RepoRoot

    # Two triggers, because one is not enough on a machine that resets.
    #
    # The logon trigger is the fast path -- it resumes a few minutes after
    # someone logs back in. On its own it is fragile: it fires on a logon
    # EVENT, so a session restored without one, or a reset at 05:00 with
    # nobody there to log in, leaves the batch stopped indefinitely. That was
    # observed: a reset at 14:21 did not resume.
    #
    # The repeating trigger is the safety net -- every $PollMinutes, forever.
    # It is safe to fire constantly because the run path refuses to start when
    # a batch is already going, and exits immediately when there is nothing
    # left to do. Cost of a spurious wake is one process spawn.
    #
    # Neither covers a reset with no user session at all. A GPU job needs an
    # interactive session; running as SYSTEM in session 0 cannot enumerate the
    # adapter. Genuinely unattended boot-resume would need auto-logon or a
    # stored password, which is a decision for whoever owns the machine.
    $logon = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
    $logon.Delay = "PT${DelayMinutes}M"        # let the display driver settle first
    $poll = New-ScheduledTaskTrigger -Once -At (Get-Date).Date `
        -RepetitionInterval (New-TimeSpan -Minutes $PollMinutes)
    $trigger = @($logon, $poll)
    $settings = New-ScheduledTaskSettingsSet `
        -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit (New-TimeSpan -Hours 24) `
        -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 10) `
        -StartWhenAvailable `
        -DontStopOnIdleEnd `
        -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

    if (Get-ScheduledTask -TaskName $TaskName -EA SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Settings $settings `
        -Description 'Resume the Nagraj transcription batch after an unexpected reboot.' | Out-Null

    $j = Get-Journal $Out
    Write-Journal $j "INSTALL  task=$TaskName delay=${DelayMinutes}m poll=${PollMinutes}m workers=$Workers out=$Out"
    Write-Host ""
    Write-Host "Registered '$TaskName'. Fires $DelayMinutes min after logon, and every $PollMinutes min thereafter."
    Write-Host "It will NOT start a run now. Journal: $j"
    Write-Host "Remove it with:  .\Scripts\_transcribe_autoresume.ps1 -Uninstall"
    return
}

# -------------------------------------------------------------- uninstall ----
if ($Uninstall) {
    if (Get-ScheduledTask -TaskName $TaskName -EA SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed scheduled task '$TaskName'."
    } else {
        Write-Host "No scheduled task '$TaskName' registered."
    }
    return
}

# ------------------------------------------------------------------ status ---
if ($PSCmdlet.ParameterSetName -eq 'Status') {
    $t = Get-ScheduledTask -TaskName $TaskName -EA SilentlyContinue
    if (-not $t) {
        Write-Host "Task '$TaskName' is not registered."
    } else {
        $i = $t | Get-ScheduledTaskInfo
        Write-Host "Task '$TaskName': state=$($t.State)"
        Write-Host "  last run : $($i.LastRunTime)  result=$($i.LastTaskResult)"
        Write-Host "  next run : $($i.NextRunTime)"
        $arg = $t.Actions[0].Arguments
        if ($arg -match '-Out\s+"([^"]+)"') {
            $j = Get-Journal $Matches[1]
            if (Test-Path $j) {
                Write-Host "`n--- journal tail ($j) ---"
                Get-Content $j -Tail 20
            }
        }
    }
    Write-Host "`n--- unexpected restarts (Kernel-Power 41) ---"
    Get-WinEvent -FilterHashtable @{LogName = 'System'; Id = 41 } -MaxEvents 5 -EA SilentlyContinue |
        ForEach-Object { "  {0}  bugcheck={1}" -f $_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss'), $_.Properties[2].Value }
    return
}

# --------------------------------------------------------------------- run ---
$journal = Get-Journal $Out
$lock = Join-Path $Out '.autoresume.lock'

# Single instance, checked two ways. The lock only knows about runs this script
# started -- a batch launched by hand holds no lock, and starting a second one
# beside it would double GPU load and race two writers onto the same .txt. So
# look for the actual work first, and treat the lock as the narrow guard for the
# window before whisper-cli has spawned.
$busy = @(Get-Process whisper-cli -EA SilentlyContinue)
if (-not $busy) {
    $busy = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -EA SilentlyContinue |
        Where-Object { $_.CommandLine -match '_transcribe_batch' })
}
if ($busy) {
    Write-Journal $journal "SKIP     a batch is already running (pid $($busy[0].Id)$($busy[0].ProcessId))"
    return
}

# A stale lock from a machine reset mid-run must not block the resume it exists
# to enable, so verify the PID is actually alive before honouring it.
if (Test-Path $lock) {
    $old = (Get-Content $lock -EA SilentlyContinue | Select-Object -First 1)
    $alive = $null
    if ($old) { $alive = Get-Process -Id ([int]$old) -EA SilentlyContinue }
    if ($alive) {
        Write-Journal $journal "SKIP     already running as pid $old"
        return
    }
    Write-Journal $journal "STALE    lock from dead pid $old (machine was reset mid-run) - clearing"
    Remove-Item $lock -Force
}

$boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
$sinceBoot = [math]::Round(((Get-Date) - $boot).TotalMinutes, 1)
$doneBefore = @(Get-ChildItem $Out -Filter *.txt -EA SilentlyContinue).Count
Write-Journal $journal "START    booted $($boot.ToString('yyyy-MM-dd HH:mm:ss')) (${sinceBoot}m ago), $doneBefore already transcribed, workers=$Workers"

# The display driver is not necessarily ready the instant a session starts, and
# a Vulkan init failure here would burn the whole resume. Wait for the adapter.
for ($i = 0; $i -lt 10; $i++) {
    $gpu = Get-CimInstance Win32_VideoController -EA SilentlyContinue |
        Where-Object { $_.Status -eq 'OK' -and $_.AdapterRAM -ne $null }
    if ($gpu) { break }
    Start-Sleep -Seconds 15
}
if (-not $gpu) { Write-Journal $journal "WARN     no healthy display adapter after 150s - trying anyway" }

$env:PYTHONIOENCODING = 'utf-8'
[System.IO.File]::WriteAllText($lock, "$PID")
$sw = [Diagnostics.Stopwatch]::StartNew()
$output = ''
try {
    $output = & $Python $BatchPy --manifest $Manifest --audio $Audio --out $Out --workers $Workers 2>&1 | Out-String
    $code = $LASTEXITCODE
} catch {
    $output = $_.Exception.Message
    $code = -1
} finally {
    Remove-Item $lock -Force -EA SilentlyContinue
}

$doneAfter = @(Get-ChildItem $Out -Filter *.txt -EA SilentlyContinue).Count
$mins = [math]::Round($sw.Elapsed.TotalMinutes, 1)
Write-Journal $journal ("EXIT     code=$code  +{0} transcripts ({1} total) in ${mins}m" -f ($doneAfter - $doneBefore), $doneAfter)
Add-Content -Path $journal -Value $output -Encoding utf8

if ($output -match 'nothing to do' -and -not $KeepEnabled) {
    Disable-ScheduledTask -TaskName $TaskName -EA SilentlyContinue | Out-Null
    Write-Journal $journal "DISABLED corpus complete - task disabled. Re-enable with -Install after adding recordings."
}
