#!/bin/bash

echo "Installing citation system dependencies..."
echo ""

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "Error: Must be run from the frontend directory"
    exit 1
fi

# Install Radix UI dependencies
echo "📦 Installing @radix-ui/react-hover-card..."
npm install @radix-ui/react-hover-card

echo "📦 Installing @radix-ui/react-scroll-area..."
npm install @radix-ui/react-scroll-area

echo ""
echo "✅ Citation system dependencies installed!"
echo ""
echo "Next steps:"
echo "1. Run 'npm run dev' to start the development server"
echo "2. Test the enhanced citation system in the chat"
echo "3. See CITATION_SYSTEM.md for full documentation"
