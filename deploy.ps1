# Скрипт для деплоя UI на GitHub Pages

Write-Host "🔨 Начинаем сборку приложения..." -ForegroundColor Cyan

# Переходим в папку web и собираем приложение
Set-Location web
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при сборке приложения!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Возвращаемся в корень проекта
Set-Location ..

Write-Host "📦 Копируем файлы в docs..." -ForegroundColor Cyan

# Удаляем старую папку docs
Remove-Item -Recurse -Force docs -ErrorAction SilentlyContinue

# Копируем собранное приложение в docs
Copy-Item -Recurse web\out docs

# Копируем .nojekyll файл
Copy-Item .nojekyll docs\

Write-Host "✅ Сборка завершена!" -ForegroundColor Green

Write-Host "📤 Коммитим и пушим изменения..." -ForegroundColor Cyan

# Добавляем изменения в git
git add .
git commit -m "Deploy UI to GitHub Pages"
git push origin master

if ($LASTEXITCODE -eq 0) {
    Write-Host "🎉 Деплой успешно завершен!" -ForegroundColor Green
    Write-Host "🌐 Приложение будет доступно по адресу: https://magneticdogson.github.io/Ask_me_bot/" -ForegroundColor Yellow
}
else {
    Write-Host "⚠️ Ошибка при пуше в GitHub!" -ForegroundColor Red
}
