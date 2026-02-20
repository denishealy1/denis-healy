import { jsPDF } from "jspdf";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

type PdfIntervention = {
  id?: string;
  interventionAt: string;
  equipmentId: string;
  zone: string;
  category: string;
  description: string;
  durationMinutes: number;
  severityScore: number;
  occurrenceScore: number;
  detectionScore: number;
  status: "pending" | "approved" | "rejected";
  qaNotes: string | null;
  reviewedAt: string | null;
  createdAt?: string;
  companyThreshold?: number;
};

const warningText =
  "NOTICE: PORTFOLIO PROJECT — NON-GMP COMPLIANT — NOT VALIDATED FOR GxP USE. DO NOT USE FOR MANUFACTURING RECORDS.";

function renderTimestamp(value: string | null | undefined) {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toISOString();
}

function buildPdf(intervention: PdfIntervention) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  const rpn =
    intervention.severityScore *
    intervention.occurrenceScore *
    intervention.detectionScore;
  const threshold = intervention.companyThreshold ?? 25;
  const highRisk = rpn > threshold;

  let y = 36;

  doc.setFillColor(254, 243, 199);
  doc.setDrawColor(245, 158, 11);
  doc.rect(32, y, pageWidth - 64, 34, "FD");
  doc.setFont("helvetica", "bold");
  doc.setTextColor(146, 64, 14);
  doc.setFontSize(8);
  doc.text(warningText, 38, y + 13, { maxWidth: pageWidth - 76 });
  y += 50;

  doc.setTextColor(156, 163, 175);
  doc.setFontSize(30);
  doc.text("PORTFOLIO · NON-GMP · MARK HEALY", pageWidth / 2, pageHeight / 2, {
    align: "center",
    angle: -24,
  });

  doc.setTextColor(55, 65, 81);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10);
  doc.text("Property of Mark Healy", 32, y);
  y += 18;

  doc.setTextColor(17, 24, 39);
  doc.setFontSize(16);
  doc.text("Annex 1 Intervention Risk Assessor Report", 32, y);
  y += 24;

  doc.setFontSize(11);
  doc.text("Intervention Details", 32, y);
  y += 14;
  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");

  const details: Array<[string, string]> = [
    ["Record ID", intervention.id ?? "-"],
    ["Status", intervention.status],
    ["Intervention At", renderTimestamp(intervention.interventionAt)],
    ["Equipment", intervention.equipmentId],
    ["Zone", intervention.zone],
    ["Category", intervention.category],
    ["Duration (minutes)", String(intervention.durationMinutes)],
  ];

  details.forEach(([label, value]) => {
    doc.setFont("helvetica", "bold");
    doc.text(`${label}:`, 36, y);
    doc.setFont("helvetica", "normal");
    doc.text(value, 150, y, { maxWidth: pageWidth - 180 });
    y += 14;
  });

  doc.setFont("helvetica", "bold");
  doc.text("Description:", 36, y);
  doc.setFont("helvetica", "normal");
  const descLines = doc.splitTextToSize(intervention.description, pageWidth - 180);
  doc.text(descLines, 150, y);
  y += Math.max(14, descLines.length * 12 + 2);

  y += 8;
  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.text("FMEA / Risk Outcome", 32, y);
  y += 14;

  doc.setFontSize(10);
  const fmeaRows: Array<[string, string]> = [
    ["Severity (S)", String(intervention.severityScore)],
    ["Occurrence (O)", String(intervention.occurrenceScore)],
    ["Detection (D)", String(intervention.detectionScore)],
    ["Computed RPN", String(rpn)],
    [
      "High-Risk Flag",
      highRisk ? `High Risk (>${threshold})` : `Within Threshold (≤${threshold})`,
    ],
  ];

  fmeaRows.forEach(([label, value]) => {
    doc.setFont("helvetica", "bold");
    doc.text(`${label}:`, 36, y);
    doc.setFont("helvetica", "normal");
    doc.text(value, 150, y);
    y += 14;
  });

  y += 8;
  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.text("QA Decision", 32, y);
  y += 14;

  doc.setFontSize(10);
  const qaRows: Array<[string, string]> = [
    ["Decision", intervention.status],
    ["QA Notes", intervention.qaNotes ?? "-"],
    ["Reviewed At", renderTimestamp(intervention.reviewedAt)],
    ["Created At", renderTimestamp(intervention.createdAt)],
  ];

  qaRows.forEach(([label, value]) => {
    doc.setFont("helvetica", "bold");
    doc.text(`${label}:`, 36, y);
    doc.setFont("helvetica", "normal");
    const lines = doc.splitTextToSize(value, pageWidth - 180);
    doc.text(lines, 150, y);
    y += Math.max(14, lines.length * 12 + 2);
  });

  doc.setDrawColor(209, 213, 219);
  doc.line(32, pageHeight - 40, pageWidth - 32, pageHeight - 40);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(124, 45, 18);
  doc.setFontSize(8);
  doc.text(warningText, 32, pageHeight - 28, { maxWidth: pageWidth - 64 });
  doc.setTextColor(55, 65, 81);
  doc.text("Property of Mark Healy", 32, pageHeight - 14);

  return Buffer.from(doc.output("arraybuffer"));
}

export async function POST(request: Request) {
  const payload = (await request.json()) as { intervention?: PdfIntervention };

  if (!payload.intervention) {
    return NextResponse.json(
      { error: "Missing intervention payload." },
      { status: 400 },
    );
  }

  const pdfBuffer = buildPdf(payload.intervention);
  const filename = `intervention-${payload.intervention.id ?? "report"}.pdf`;

  return new NextResponse(pdfBuffer, {
    status: 200,
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `attachment; filename="${filename}"`,
    },
  });
}
