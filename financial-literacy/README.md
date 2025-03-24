# HabitHero Landing Page

A modern, mobile-first landing page for a habit tracking app. This website is designed to showcase the app's features and convert visitors into users.

## Features

- **Responsive Design**: Fully responsive design that looks great on all devices
- **Mobile-First**: Built with a mobile-first approach
- **Modern UI**: Clean, modern interface with a focus on conversion
- **Performance**: Fast loading with minimal dependencies
- **Animations**: Subtle animations for enhanced user experience
- **Interactive Elements**: Interactive components to engage users

## File Structure

- `index.html` - The main HTML file
- `styles.css` - CSS styling
- `script.js` - JavaScript functionality
- `README.md` - This documentation file

## Technologies Used

This project uses only:
- HTML5
- CSS3
- Vanilla JavaScript

No frameworks, libraries, or build tools were used to keep it simple and lightweight.

## How to Use

1. Download or clone this repository
2. Open `index.html` in your web browser
3. To make changes:
   - Edit `index.html` for content changes
   - Modify `styles.css` for styling changes
   - Update `script.js` for functionality changes

## Customization

### Changing Colors

The main colors are defined as CSS variables in the `:root` selector in `styles.css`. You can easily change the color scheme by modifying these variables:

```css
:root {
    --primary-color: #4F46E5;
    --primary-hover: #4338CA;
    /* other color variables */
}
```

### Changing Content

To change the content of the page, edit the text in `index.html`. The structure is organized into sections:

1. Hero section
2. Feature sections (3 sections)
3. CTA (Call to Action) section
4. Footer

### Changing Images

The website uses SVG illustrations generated directly in the HTML. You can replace them with your own images by:

1. Adding image files to your project folder
2. Replacing the SVG code in the HTML with image tags pointing to your files, like:
   ```html
   <img src="path/to/your/image.jpg" alt="Description">
   ```

## Browser Compatibility

This website works on all modern browsers:
- Chrome
- Firefox
- Safari
- Edge

## License

Free to use for personal and commercial projects.

---

Created for the HabitHero app landing page project. 