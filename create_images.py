"""
Create simple dummy PNG images for the illustration system.
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    # Create assets/images directory if it doesn't exist
    os.makedirs("assets/images", exist_ok=True)
    
    # Dummy field categories
    fields = [
        ("position_reference", "Position Reference"),
        ("position_x", "X Position"),
        ("position_y", "Y Position"),
        ("stock_x", "Stock X Size"),
        ("stock_y", "Stock Y Size"),
        ("stock_z", "Stock Z Size"),
        ("stock_z_height", "Finished Z Height"),
        ("roughing_tool", "Roughing Tool"),
        ("roughing_strategy", "Roughing Strategy"),
        ("roughing_depth", "Depth of Cut"),
        ("roughing_leave", "Leave for Finishing"),
        ("roughing_width", "Width of Cut"),
        ("roughing_rpm", "Roughing RPM"),
        ("roughing_feedrate", "Roughing Feedrate"),
        ("finishing_tool", "Finishing Tool"),
        ("finishing_strategy", "Finishing Strategy"),
        ("finishing_width", "Finishing Width"),
        ("finishing_rpm", "Finishing RPM"),
        ("finishing_feedrate", "Finishing Feedrate"),
    ]
    
    for field_id, field_name in fields:
        # Create image
        img = Image.new('RGB', (300, 200), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Add text
        draw.text((10, 10), field_name, fill='black')
        draw.text((10, 40), "[Illustration Placeholder]", fill='gray')
        draw.text((10, 70), f"Field: {field_id}", fill='gray')
        
        # Draw a simple border
        draw.rectangle([5, 5, 295, 195], outline='black', width=2)
        
        # Save image
        filename = f"assets/images/{field_id}.png"
        img.save(filename)
        print(f"Created: {filename}")
    
    print("\nDummy images created successfully!")
    
except ImportError:
    print("PIL/Pillow not installed. Creating placeholder files instead.")
    print("To generate proper images, install Pillow: pip install Pillow")
    print("\nTo create images later, run: python create_images.py")
