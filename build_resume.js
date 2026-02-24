const { Document, Packer, Paragraph, TextRun, AlignmentType, LevelFormat, BorderStyle, HeadingLevel } = require('docx');
const fs = require('fs');

const data = JSON.parse(fs.readFileSync(process.argv[3] || '/tmp/resume_data.json', 'utf8'));

// ── Helpers ───────────────────────────────────────────────────────────────────

function hline() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2E75B6", space: 1 } },
    spacing: { after: 80 },
    children: [],
  });
}

function sectionHeader(text) {
  return new Paragraph({
    children: [new TextRun({ text: text.toUpperCase(), bold: true, size: 22, color: "2E75B6", font: "Arial" })],
    spacing: { before: 200, after: 60 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "2E75B6", space: 1 } },
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun({ text, size: 20, font: "Arial" })],
    spacing: { after: 40 },
  });
}

function spacer(pts = 80) {
  return new Paragraph({ children: [], spacing: { after: pts } });
}

// ── Build document ────────────────────────────────────────────────────────────

const children = [];

// Name
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: data.name, bold: true, size: 32, font: "Arial", color: "1E3A5F" })],
  spacing: { after: 60 },
}));

// Contact line
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: data.contact, size: 18, font: "Arial", color: "555555" })],
  spacing: { after: 160 },
}));

// Summary
if (data.tailored.summary) {
  children.push(sectionHeader("Professional Summary"));
  children.push(new Paragraph({
    children: [new TextRun({ text: data.tailored.summary, size: 20, font: "Arial", italics: true })],
    spacing: { after: 120 },
  }));
}

// Education
children.push(sectionHeader("Education"));
for (const edu of data.education) {
  children.push(new Paragraph({
    children: [
      new TextRun({ text: edu.degree, bold: true, size: 20, font: "Arial" }),
      new TextRun({ text: "  |  " + edu.school, size: 20, font: "Arial", color: "555555" }),
      new TextRun({ text: "  " + edu.dates, size: 20, font: "Arial", color: "888888" }),
    ],
    spacing: { after: 40 },
  }));
  if (edu.note) {
    children.push(new Paragraph({
      children: [new TextRun({ text: edu.note, size: 18, font: "Arial", color: "555555", italics: true })],
      spacing: { after: 80 },
    }));
  }
}

// Skills
children.push(sectionHeader("Technical Skills"));
const skills = data.tailored.skills;
for (const [category, items] of Object.entries(skills)) {
  if (items && items.length > 0) {
    children.push(new Paragraph({
      children: [
        new TextRun({ text: category + ": ", bold: true, size: 20, font: "Arial" }),
        new TextRun({ text: items.join(", "), size: 20, font: "Arial" }),
      ],
      spacing: { after: 50 },
    }));
  }
}

// Experience
children.push(sectionHeader("Professional Experience"));
for (const exp of data.tailored.experience) {
  children.push(new Paragraph({
    children: [
      new TextRun({ text: exp.title, bold: true, size: 20, font: "Arial" }),
      new TextRun({ text: "  |  " + exp.company, size: 20, font: "Arial", color: "555555" }),
      new TextRun({ text: "  " + exp.dates, size: 20, font: "Arial", color: "888888" }),
    ],
    spacing: { after: 50 },
  }));
  for (const b of exp.bullets) {
    children.push(bullet(b));
  }
  children.push(spacer(60));
}

// Projects
children.push(sectionHeader("Technical Projects"));
for (const proj of data.tailored.projects) {
  children.push(new Paragraph({
    children: [
      new TextRun({ text: proj.name, bold: true, size: 20, font: "Arial" }),
      new TextRun({ text: "  " + (proj.dates || ""), size: 20, font: "Arial", color: "888888" }),
    ],
    spacing: { after: 50 },
  }));
  for (const b of proj.bullets) {
    children.push(bullet(b));
  }
  children.push(spacer(60));
}

// Additional
if (data.additional) {
  children.push(sectionHeader("Additional Information"));
  for (const line of data.additional) {
    children.push(new Paragraph({
      children: [new TextRun({ text: line, size: 20, font: "Arial" })],
      spacing: { after: 50 },
    }));
  }
}

// ── Assemble ──────────────────────────────────────────────────────────────────

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 480, hanging: 240 } } },
      }],
    }],
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 900, right: 1080, bottom: 900, left: 1080 },
      },
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(process.argv[2] || 'tailored_resume.docx', buf);
  console.log('OK');
});