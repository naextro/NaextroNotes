# 📚 Naextro's Notes

A simple subject-wise notes holder for organizing and sharing study materials.

## 🌟 Features

- **📚 Subject-Wise Organization**: Keep your notes organized by subject and date for easy access
- **👥 Simple Sharing**: Share your study notes easily with friends and study groups
- **🔍 Quick Search**: Find your notes quickly with simple filtering by subject and date
- **👁️ Full-Screen Preview**: Preview notes in high quality before downloading
- **📥 Easy Download**: Download individual notes or entire collections
- **📱 Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **🌙 Dark Theme**: Easy on the eyes for long study sessions

## 🚀 Getting Started

### Prerequisites

- A modern web browser (Chrome, Firefox, Safari, Edge)
- A local web server (optional, for development)

### Installation

1. **Clone or download** this repository
2. **Place your notes** in the `images/` directory following the date-based folder structure:
   ```
   images/
   ├── 10-10-2025/
   │   ├── chem1.jpg
   │   └── phy1.jpg
   ├── 11-10-2025/
   │   ├── chem.jpg
   │   └── phy.jpg
   └── ...
   ```

3. **Update the data** in `info.json` to match your notes structure:
   ```json
   [
     {
       "date": "10-10-2025",
       "subjects": [
         {
           "subject": "Chemistry",
           "images": ["images/10-10-2025/chem1.jpg"]
         },
         {
           "subject": "Physics", 
           "images": ["images/10-10-2025/phy1.jpg"]
         }
       ]
     }
   ]
   ```

4. **Open** `index.html` in your web browser

### Running Locally

For development or if you encounter CORS issues:

```bash
# Using Python 3
python -m http.server 8000

# Using Python 2
python -m SimpleHTTPServer 8000

# Using Node.js (if you have http-server installed)
npx http-server

# Using PHP
php -S localhost:8000
```

Then visit `http://localhost:8000` in your browser.

## 📁 Project Structure

```
Naextro's Notes/
├── index.html          # Main HTML file
├── style.css           # Styling and responsive design
├── script.js           # JavaScript functionality
├── info.json           # Notes metadata and structure
├── images/             # Notes images directory
│   ├── 10-10-2025/     # Date-based folders
│   ├── 11-10-2025/
│   └── ...
└── README.md           # This file
```

## 🎯 Usage

### Adding New Notes

1. **Create a date folder** in `images/` (format: DD-MM-YYYY)
2. **Add your note images** to the folder
3. **Update `info.json`** with the new date and subject information
4. **Refresh** the page to see your new notes

### Filtering Notes

- **Subject Filter**: Filter notes by specific subjects (Chemistry, Physics, etc.)
- **Date Filter**: Filter by day, month, or year
- **Combined Filters**: Use both subject and date filters together

### Previewing Notes

- Click the **👁️ Preview** button to view notes in full-screen
- Use **Escape** key or click outside to close the preview
- Click the **×** button to close the preview

### Downloading Notes

- Click the **📥 Download** button to save individual notes
- Notes are automatically named with subject and date information

## 🛠️ Customization

### Styling

Edit `style.css` to customize:
- Color scheme (CSS variables in `:root`)
- Fonts and typography
- Layout and spacing
- Responsive breakpoints

### Functionality

Edit `script.js` to add:
- New filtering options
- Additional image formats
- Custom download behaviors
- Integration with external services

## 📱 Browser Support

- ✅ Chrome 60+
- ✅ Firefox 55+
- ✅ Safari 12+
- ✅ Edge 79+

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Built with vanilla HTML, CSS, and JavaScript
- Uses modern CSS Grid and Flexbox for responsive layouts
- Inspired by the need for simple, effective note organization

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page
2. Create a new issue with detailed information
3. Include browser version and steps to reproduce

---

**Happy Studying! 📚✨**
