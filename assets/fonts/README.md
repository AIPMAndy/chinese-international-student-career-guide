# PDF build fonts

Font binaries are not distributed. To rebuild the PDF, obtain NotoSansSC-VF.ttf from the official notofonts/noto-cjk project and run `python3 scripts/build_pdf.py --font-source /path/to/NotoSansSC-VF.ttf`. Temporary subsets stay local. The published PDF already embeds the glyphs it needs. See OFL.txt for upstream licensing.
