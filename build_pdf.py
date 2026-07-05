import os
import subprocess
import sys
import glob

# Ensure required libraries are installed
try:
    import markdown
    from pygments.formatters import HtmlFormatter
except ImportError:
    print("Installing markdown and pygments...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "markdown", "pygments"])
    import markdown
    from pygments.formatters import HtmlFormatter

def build_pdf():
    rust_dir = "/Users/kadmin/repos/gemini_apps/tt/RustTopics"
    output_html = os.path.join(rust_dir, "sample-rusttopics.html")
    output_pdf = os.path.join(rust_dir, "sample-rusttopics.pdf")
    output_pdf_root = "/Users/kadmin/repos/gemini_apps/tt/sample-rusttopics.pdf"

    # Gather all markdown files sorted alphabetically
    md_files = sorted(glob.glob(os.path.join(rust_dir, "*.md")))
    print(f"Found {len(md_files)} markdown files to compile.")

    md_extensions = ['fenced_code', 'codehilite', 'tables', 'toc', 'sane_lists']
    
    toc_items = []
    topics_html = ""

    for idx, md_file in enumerate(md_files):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Clean up LaTeX math arrows and symbols so they render cleanly in PDF
        content = content.replace("$\\rightarrow$", "→")
        content = content.replace("$\\to$", "→")
        content = content.replace("$\\Rightarrow$", "⇒")
        content = content.replace("$\\leftarrow$", "←")
        content = content.replace("$\\Leftarrow$", "⇐")
        content = content.replace("$\\leftrightarrow$", "↔")
        content = content.replace("$\\Leftrightarrow$", "⇔")
        content = content.replace("\\rightarrow", "→")
        content = content.replace("\\to", "→")

        # Extract the first heading (# Title or ## Title) as the topic name
        title = os.path.basename(md_file)
        for line in content.splitlines():
            if line.startswith("# ") or line.startswith("## "):
                title = line.lstrip("# ").strip()
                break
        
        topic_id = f"topic-{idx}"
        file_badge = os.path.basename(md_file)
        
        # Add entry to TOC
        toc_items.append(
            f"<li><a href='#{topic_id}'><span class='toc-badge'>{file_badge}</span> <span class='toc-title'>{title}</span></a></li>"
        )

        # Convert markdown content to HTML
        html_body = markdown.markdown(content, extensions=md_extensions)
        
        # Add anchor ID and bidirectional jump links
        topics_html += f"""
        <div id="{topic_id}" class="topic-container">
            <div class="back-to-toc">
                <a href="#toc">⬆ Return to Table of Contents</a>
            </div>
            {html_body}
            <div class="back-to-toc bottom-link">
                <a href="#toc">⬆ Return to Table of Contents</a>
            </div>
        </div>
        <div style='page-break-after: always;'></div>
        """

    toc_html_list = "\n".join(toc_items)

    # Get Light mode (Tango/Default) CSS from Pygments
    pygments_css = HtmlFormatter(style='tango').get_style_defs('.codehilite')

    # Build full HTML document with premium light mode typography, colors, TOC, and layout
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rust Systems Programming & Architecture - Q&A Masterclass</title>
    <style>
        @page {{
            size: A4;
            margin: 20mm 15mm 20mm 15mm;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            background-color: #ffffff;
            padding: 0;
            margin: 0;
            font-size: 10pt;
        }}
        .header-title {{
            text-align: center;
            padding: 50px 0 40px 0;
            border-bottom: 3px solid #b7410e;
            margin-bottom: 40px;
            page-break-after: always;
        }}
        .header-title h1 {{
            font-size: 28pt;
            color: #b7410e; /* Official Rust Orange-Brown */
            border: none;
            margin-bottom: 10px;
            page-break-before: avoid;
        }}
        .header-title h2 {{
            font-size: 16pt;
            color: #444444;
            border: none;
            margin-top: 0;
            font-weight: 300;
            padding-left: 0;
        }}
        .header-title p {{
            font-size: 10pt;
            color: #777777;
            margin-top: 30px;
        }}
        /* Table of Contents Styling */
        .toc-page {{
            page-break-after: always;
            padding: 10px 0;
        }}
        .toc-page h1 {{
            font-size: 24pt;
            color: #1a365d;
            border-bottom: 3px solid #3182ce;
            padding-bottom: 10px;
            margin-top: 0;
            margin-bottom: 25px;
            page-break-before: avoid;
        }}
        .toc-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .toc-list li {{
            margin-bottom: 10px;
            border-bottom: 1px dashed #e2e8f0;
            padding-bottom: 6px;
        }}
        .toc-list a {{
            text-decoration: none;
            color: #2b6cb0;
            display: flex;
            align-items: baseline;
            font-size: 10.5pt;
        }}
        .toc-badge {{
            font-family: "JetBrains Mono", "Fira Code", monospace;
            font-size: 8pt;
            background-color: #edf2f7;
            color: #4a5568;
            padding: 2px 7px;
            border-radius: 4px;
            margin-right: 12px;
            font-weight: 600;
            min-width: 90px;
            display: inline-block;
            text-align: center;
        }}
        .toc-title {{
            font-weight: 500;
            color: #1a202c;
        }}
        /* Back to TOC Link Button */
        .back-to-toc {{
            text-align: right;
            margin-bottom: 15px;
            margin-top: 10px;
        }}
        .back-to-toc.bottom-link {{
            margin-top: 35px;
            margin-bottom: 10px;
            border-top: 1px solid #edf2f7;
            padding-top: 12px;
        }}
        .back-to-toc a {{
            font-size: 8.5pt;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            color: #b7410e;
            text-decoration: none;
            background-color: #fffaf0;
            border: 1px solid #fbd38d;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 600;
            display: inline-block;
        }}
        /* Content Headings & Text */
        h1 {{
            font-size: 22pt;
            color: #b7410e;
            border-bottom: 2px solid #e1e4e8;
            padding-bottom: 8px;
            margin-top: 25px;
            margin-bottom: 20px;
            page-break-before: avoid;
            page-break-after: avoid;
        }}
        h2 {{
            font-size: 14.5pt;
            color: #1a365d;
            margin-top: 25px;
            margin-bottom: 12px;
            border-left: 4px solid #3182ce;
            padding-left: 10px;
            page-break-after: avoid;
        }}
        h3 {{
            font-size: 12pt;
            color: #2b6cb0;
            margin-top: 20px;
            margin-bottom: 8px;
            page-break-after: avoid;
        }}
        h4, h5 {{
            font-size: 10.5pt;
            color: #4a5568;
            margin-top: 16px;
            margin-bottom: 6px;
            page-break-after: avoid;
        }}
        p, ul, ol {{
            margin-bottom: 12px;
            padding-left: 4px;
        }}
        ul, ol {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 5px;
            line-height: 1.5;
        }}
        code {{
            font-family: "JetBrains Mono", "Fira Code", Menlo, Monaco, Consolas, monospace;
            font-size: 8.5pt;
            background-color: #f1f5f9;
            color: #c53030;
            padding: 2px 5px;
            border-radius: 4px;
            border: 1px solid #e2e8f0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        /* Light Mode Code Block Styling - Single Simple Enclosure Box */
        .codehilite {{
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
        }}
        pre {{
            background-color: #f8fafc !important; /* Light slate background */
            color: #1e293b !important; /* Dark slate text */
            padding: 14px;
            border-radius: 6px;
            font-family: "JetBrains Mono", "Fira Code", Menlo, Monaco, Consolas, monospace;
            font-size: 8.5pt;
            line-height: 1.45;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            page-break-inside: avoid;
            margin-top: 10px;
            margin-bottom: 18px;
            border: 1px solid #cbd5e1 !important; /* One single crisp slate border */
            white-space: pre-wrap !important; /* Force wrapping of long lines and comments */
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            word-break: break-all !important;
        }}
        pre code {{
            background-color: transparent !important;
            color: inherit !important;
            padding: 0 !important;
            border: none !important;
            border-radius: 0 !important;
            font-size: inherit;
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            word-break: break-all !important;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 18px;
            margin-bottom: 22px;
            font-size: 9pt;
            page-break-inside: avoid;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            border-radius: 6px;
            overflow: hidden;
        }}
        th, td {{
            border: 1px solid #e2e8f0;
            padding: 10px 14px;
            text-align: left;
        }}
        th {{
            background-color: #edf2f7;
            color: #1a202c;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f7fafc;
        }}
        blockquote {{
            border-left: 4px solid #dd6b20;
            background-color: #fffaf0;
            margin: 16px 0;
            padding: 12px 18px;
            color: #4a5568;
            font-style: italic;
            border-radius: 0 6px 6px 0;
            page-break-inside: avoid;
        }}
        hr {{
            border: none;
            height: 1px;
            background-color: #e2e8f0;
            margin: 30px 0;
        }}
        {pygments_css}
    </style>
</head>
<body>
    <div class="header-title">
        <h1>Rust Systems Programming & Architecture</h1>
        <h2>The Complete Technical Q&A Series (Topics 000–016)</h2>
        <p>Compiled by Antigravity AI • DeepMind Advanced Agentic Coding</p>
    </div>

    <!-- Table of Contents Page -->
    <div id="toc" class="toc-page">
        <h1>Table of Contents</h1>
        <ul class="toc-list">
            {toc_html_list}
        </ul>
    </div>

    <!-- All Topics Content -->
    {topics_html}
</body>
</html>
"""

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Generated HTML with light mode, wrapping fix, and clean arrows: {output_html}")

    # Use Google Chrome Headless to generate high-res PDF
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not os.path.exists(chrome_path):
        print("Google Chrome not found at default path. Checking fallback...")
        chrome_path = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"

    print(f"Using browser for PDF generation: {chrome_path}")
    cmd = [
        chrome_path,
        "--headless=new",
        "--no-sandbox",
        "--disable-crash-reporter",
        "--disable-dev-shm-usage",
        "--allow-file-access-from-files",
        "--disable-gpu",
        f"--print-to-pdf={output_pdf}",
        output_html
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully generated PDF with Chrome: {output_pdf}")
    except Exception as e:
        print(f"Chrome PDF generation failed ({e}). Falling back to weasyprint...")
        try:
            import weasyprint
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "weasyprint"])
            import weasyprint
        weasyprint.HTML(filename=output_html).write_pdf(output_pdf)
        print(f"Successfully generated PDF with WeasyPrint: {output_pdf}")

    # Also copy to root tt folder for convenience
    import shutil
    shutil.copyfile(output_pdf, output_pdf_root)
    print(f"Copied PDF to: {output_pdf_root}")

if __name__ == "__main__":
    build_pdf()
