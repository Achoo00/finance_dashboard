$directories = @(
    "app\database\models",
    "app\database\repositories",
    "app\domain\entities",
    "app\domain\services",
    "app\api\clients",
    "app\api\schemas",
    "app\ui\components\layout",
    "app\ui\components\charts",
    "app\ui\components\forms",
    "app\ui\pages\dashboard",
    "app\ui\pages\portfolio",
    "app\ui\pages\settings",
    "app\utils"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created directory: $dir"
    } else {
        Write-Host "Directory already exists: $dir"
    }
}

# Create __init__.py files
$initFiles = @(
    "app\__init__.py",
    "app\config\__init__.py",
    "app\database\__init__.py",
    "app\database\models\__init__.py",
    "app\database\repositories\__init__.py",
    "app\domain\__init__.py",
    "app\domain\entities\__init__.py",
    "app\domain\services\__init__.py",
    "app\api\__init__.py",
    "app\api\clients\__init__.py",
    "app\api\schemas\__init__.py",
    "app\ui\__init__.py",
    "app\ui\components\__init__.py",
    "app\ui\components\layout\__init__.py",
    "app\ui\components\charts\__init__.py",
    "app\ui\components\forms\__init__.py",
    "app\ui\pages\__init__.py",
    "app\ui\pages\dashboard\__init__.py",
    "app\ui\pages\portfolio\__init__.py",
    "app\ui\pages\settings\__init__.py",
    "app\utils\__init__.py"
)

foreach ($file in $initFiles) {
    if (-not (Test-Path $file)) {
        New-Item -ItemType File -Path $file -Force | Out-Null
        Write-Host "Created file: $file"
    } else {
        Write-Host "File already exists: $file"
    }
}
