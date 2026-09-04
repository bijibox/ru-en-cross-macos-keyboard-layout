#!/usr/bin/env swift
// Rebuild the checked-in vector-drawn ICNS assets with the macOS system font.
// Uses only AppKit/CoreText. No input source, preference, or UI changes.
import AppKit
import CoreText

let output = URL(fileURLWithPath: CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "assets/icons")
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)

func icon(_ label: String, pixels: Int) -> NSBitmapImageRep {
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: pixels, pixelsHigh: pixels,
                              bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                              colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    let context = NSGraphicsContext(bitmapImageRep: rep)!.cgContext
    context.scaleBy(x: CGFloat(pixels) / 16, y: CGFloat(pixels) / 16)
    let bounds = CGRect(x: 0, y: 0, width: 16, height: 16)
    context.clear(bounds)
    context.setFillColor(NSColor.black.cgColor)
    context.addPath(CGPath(roundedRect: bounds, cornerWidth: 2.75, cornerHeight: 2.75, transform: nil))
    context.fillPath()

    // Cut the glyph outlines out of the alpha mask, so macOS can tint the
    // entire icon correctly in either appearance and in selected menus.
    let font = NSFont.systemFont(ofSize: 10, weight: .medium)
    let text = NSAttributedString(string: label, attributes: [.font: font])
    let line = CTLineCreateWithAttributedString(text)
    let textBounds = CTLineGetBoundsWithOptions(line, .useGlyphPathBounds)
    let x = (16 - textBounds.width) / 2 - textBounds.minX
    let y: CGFloat = 4.75 - textBounds.minY
    context.setBlendMode(.destinationOut)
    for run in CTLineGetGlyphRuns(line) as! [CTRun] {
        let count = CTRunGetGlyphCount(run)
        var glyphs = [CGGlyph](repeating: 0, count: count)
        var positions = [CGPoint](repeating: .zero, count: count)
        CTRunGetGlyphs(run, CFRange(), &glyphs)
        CTRunGetPositions(run, CFRange(), &positions)
        let runFont = (CTRunGetAttributes(run) as NSDictionary)[kCTFontAttributeName] as! CTFont
        for i in 0..<count {
            if let path = CTFontCreatePathForGlyph(runFont, glyphs[i], nil) {
                var transform = CGAffineTransform(translationX: x + positions[i].x, y: y + positions[i].y)
                context.addPath(path.copy(using: &transform)!)
            }
        }
    }
    context.fillPath()

    // A discreet 4 × 2 pt cross-input mark below the main letters.
    context.setLineWidth(0.8)
    context.setLineCap(.round)
    context.setLineJoin(.round)
    context.setStrokeColor(NSColor.black.cgColor)
    context.move(to: CGPoint(x: 9.75, y: 2.6))
    context.addLine(to: CGPoint(x: 13.75, y: 2.6))
    context.move(to: CGPoint(x: 10.75, y: 1.6))
    context.addLine(to: CGPoint(x: 9.75, y: 2.6))
    context.addLine(to: CGPoint(x: 10.75, y: 3.6))
    context.move(to: CGPoint(x: 12.75, y: 1.6))
    context.addLine(to: CGPoint(x: 13.75, y: 2.6))
    context.addLine(to: CGPoint(x: 12.75, y: 3.6))
    context.strokePath()
    return rep
}

func uint32(_ value: Int) -> Data {
    var value = UInt32(value).bigEndian
    return withUnsafeBytes(of: &value) { Data($0) }
}

let layouts = [("USCrossRussianPC", "US"), ("RussianPCCrossUS", "РУ")]
for (name, label) in layouts {
    var chunks = Data()
    // Native-size and Retina representations, plus a larger Settings preview.
    for (tag, size) in [("icp4", 16), ("icp5", 32), ("icp6", 64),
                        ("ic11", 32), ("ic12", 64), ("ic07", 128), ("ic08", 256)] {
        let png = icon(label, pixels: size).representation(using: .png, properties: [:])!
        chunks.append(tag.data(using: .ascii)!)
        chunks.append(uint32(png.count + 8))
        chunks.append(png)
    }
    var icns = "icns".data(using: .ascii)!
    icns.append(uint32(chunks.count + 8))
    icns.append(chunks)
    try icns.write(to: output.appendingPathComponent(name + ".icns"))
    try icon(label, pixels: 64).representation(using: .png, properties: [:])!
        .write(to: output.appendingPathComponent(name + ".png"))
}

// Review the same alpha masks at 1×, 2× and an enlarged size, on both themes.
let preview = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 640, pixelsHigh: 240,
                               bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                               isPlanar: false, colorSpaceName: .deviceRGB,
                               bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
let graphics = NSGraphicsContext(bitmapImageRep: preview)!
NSGraphicsContext.current = graphics
let cg = graphics.cgContext
for column in 0..<2 {
    let left = CGFloat(column * 320)
    let background = column == 0 ? NSColor(white: 0.97, alpha: 1) : NSColor(white: 0.13, alpha: 1)
    let ink = column == 0 ? NSColor(white: 0.12, alpha: 1) : NSColor(white: 0.95, alpha: 1)
    background.setFill()
    NSRect(x: left, y: 0, width: 320, height: 240).fill()
    let title = column == 0 ? "Светлая тема" : "Тёмная тема"
    (title as NSString).draw(at: NSPoint(x: left + 24, y: 202), withAttributes: [.font: NSFont.systemFont(ofSize: 15, weight: .medium), .foregroundColor: ink])
    for (row, (_, label)) in layouts.enumerated() {
        let y = CGFloat(123 - row * 88)
        (label as NSString).draw(at: NSPoint(x: left + 24, y: y + 17), withAttributes: [.font: NSFont.systemFont(ofSize: 13), .foregroundColor: ink])
        for (offset, size) in [(90, 16), (138, 32), (212, 56)] {
            cg.saveGState()
            let rect = CGRect(x: left + CGFloat(offset), y: y + CGFloat(56-size)/2, width: CGFloat(size), height: CGFloat(size))
            cg.clip(to: rect, mask: icon(label, pixels: size).cgImage!)
            cg.setFillColor(ink.cgColor)
            cg.fill(rect)
            cg.restoreGState()
        }
    }
}
NSGraphicsContext.restoreGraphicsState()
try preview.representation(using: .png, properties: [:])!.write(to: output.appendingPathComponent("preview.png"))
print("Generated US / РУ cross icons in \(output.path)")
