import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

if __name__ == "__main__":
    from src.main import main
    import asyncio
    asyncio.run(main())
