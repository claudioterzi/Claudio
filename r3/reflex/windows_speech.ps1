param(
    [string]$Culture = "it-IT"
)

$ErrorActionPreference = "Stop"

function Write-R3Json {
    param([hashtable]$Payload)
    [Console]::Out.WriteLine(($Payload | ConvertTo-Json -Compress))
    [Console]::Out.Flush()
}

try {
    Add-Type -AssemblyName System.Speech

    try {
        $cultureInfo = [System.Globalization.CultureInfo]::GetCultureInfo($Culture)
        $engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine($cultureInfo)
    }
    catch {
        $engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
        Write-R3Json @{
            type = "status"
            status = "culture_fallback"
            requested_culture = $Culture
            active_culture = $engine.RecognizerInfo.Culture.Name
        }
    }

    $grammar = New-Object System.Speech.Recognition.DictationGrammar
    $engine.LoadGrammar($grammar)
    $engine.SetInputToDefaultAudioDevice()

    $engine.add_SpeechHypothesized({
        param($sender, $eventArgs)
        $result = $eventArgs.Result
        Write-R3Json @{
            type = "hypothesis"
            text = $result.Text
            confidence = [double]$result.Confidence
            final = $false
        }
    })

    $engine.add_SpeechRecognized({
        param($sender, $eventArgs)
        $result = $eventArgs.Result
        Write-R3Json @{
            type = "recognized"
            text = $result.Text
            confidence = [double]$result.Confidence
            final = $true
        }
    })

    $engine.add_SpeechRecognitionRejected({
        param($sender, $eventArgs)
        Write-R3Json @{
            type = "rejected"
            text = ""
            confidence = 0.0
            final = $true
        }
    })

    Write-R3Json @{
        type = "status"
        status = "ready"
        active_culture = $engine.RecognizerInfo.Culture.Name
    }

    $engine.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Multiple)
    while ($true) {
        Start-Sleep -Milliseconds 100
    }
}
catch {
    Write-R3Json @{
        type = "error"
        message = $_.Exception.Message
        final = $true
    }
    exit 2
}
finally {
    if ($null -ne $engine) {
        try { $engine.RecognizeAsyncCancel() } catch {}
        try { $engine.Dispose() } catch {}
    }
}
