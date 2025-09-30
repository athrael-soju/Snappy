@echo off
echo Installing citation system dependencies...
echo.

REM Check if package.json exists
if not exist "package.json" (
    echo Error: Must be run from the frontend directory
    exit /b 1
)

REM Install Radix UI dependencies
echo Installing @radix-ui/react-hover-card...
call npm install @radix-ui/react-hover-card

echo.
echo Installing @radix-ui/react-scroll-area...
call npm install @radix-ui/react-scroll-area

echo.
echo Citation system dependencies installed!
echo.
echo Next steps:
echo 1. Run 'npm run dev' to start the development server
echo 2. Test the enhanced citation system in the chat
echo 3. See CITATION_SYSTEM.md for full documentation
echo.
pause
