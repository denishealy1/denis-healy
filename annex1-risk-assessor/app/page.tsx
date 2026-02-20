"use client";

import { useMemo, useState } from "react";
import { PortfolioWarningBanner } from "@/components/portfolio-warning-banner";
import { supabase } from "@/lib/supabase-client";

type Zone = "Grade A" | "Grade B" | "Isolator" | "RABS";
type Category = "Routine" | "Non-routine";
type InterventionStatus = "pending" | "approved" | "rejected";
type DashboardView = "kanban" | "list";

type InterventionRecord = {
  id: string;
  interventionAt: string;
  equipmentId: string;
  zone: Zone;
  category: Category;
  description: string;
  durationMinutes: number;
  severityScore: number;
  occurrenceScore: number;
  detectionScore: number;
  status: InterventionStatus;
  qaNotes: string | null;
  reviewedAt: string | null;
};

const zones: Zone[] = ["Grade A", "Grade B", "Isolator", "RABS"];
const categories: Category[] = ["Routine", "Non-routine"];
const scores = [1, 2, 3, 4, 5];
const defaultThreshold = 25;
const qaStatuses: InterventionStatus[] = ["pending", "approved", "rejected"];

const seedInterventions: InterventionRecord[] = [
  {
    id: "5ca9c9b6-3325-43a1-9f0a-e0ea4f52a004",
    interventionAt: "2026-02-18T08:00",
    equipmentId: "FILL-LN-01",
    zone: "Grade A",
    category: "Routine",
    description: "Routine stopper bowl refill under grade A conditions.",
    durationMinutes: 9,
    severityScore: 3,
    occurrenceScore: 3,
    detectionScore: 2,
    status: "pending",
    qaNotes: null,
    reviewedAt: null,
  },
  {
    id: "1558c6dd-4c6a-4408-9a38-5bc7dfd41825",
    interventionAt: "2026-02-17T13:45",
    equipmentId: "RABS-02",
    zone: "RABS",
    category: "Non-routine",
    description: "Sensor reset intervention inside RABS chamber.",
    durationMinutes: 14,
    severityScore: 4,
    occurrenceScore: 3,
    detectionScore: 3,
    status: "pending",
    qaNotes: null,
    reviewedAt: null,
  },
  {
    id: "0d0512d6-5bef-44f1-89fd-95f8521d1c3f",
    interventionAt: "2026-02-16T11:10",
    equipmentId: "ISOL-07",
    zone: "Isolator",
    category: "Routine",
    description: "Glove replacement protocol follow-up.",
    durationMinutes: 11,
    severityScore: 2,
    occurrenceScore: 2,
    detectionScore: 2,
    status: "approved",
    qaNotes: "Reviewed and accepted. Mitigations documented in batch notes.",
    reviewedAt: "2026-02-16T12:02:00.000Z",
  },
];

function rpnForRecord(record: Pick<InterventionRecord, "severityScore" | "occurrenceScore" | "detectionScore">) {
  return record.severityScore * record.occurrenceScore * record.detectionScore;
}

export default function Home() {
  const [interventionAt, setInterventionAt] = useState("");
  const [equipmentId, setEquipmentId] = useState("");
  const [zone, setZone] = useState<Zone>("Grade A");
  const [category, setCategory] = useState<Category>("Routine");
  const [description, setDescription] = useState("");
  const [durationMinutes, setDurationMinutes] = useState<number | "">("");

  const [severityScore, setSeverityScore] = useState(1);
  const [occurrenceScore, setOccurrenceScore] = useState(1);
  const [detectionScore, setDetectionScore] = useState(1);

  const [viewMode, setViewMode] = useState<DashboardView>("kanban");
  const [interventions, setInterventions] = useState<InterventionRecord[]>(seedInterventions);
  const [qaNotesDraft, setQaNotesDraft] = useState<Record<string, string>>({});
  const [qaErrors, setQaErrors] = useState<Record<string, string>>({});
  const [qaSavingRecordId, setQaSavingRecordId] = useState<string | null>(null);

  const rpnScore = useMemo(
    () => severityScore * occurrenceScore * detectionScore,
    [severityScore, occurrenceScore, detectionScore],
  );

  const isHighRisk = rpnScore > defaultThreshold;

  const groupedInterventions = useMemo(() => {
    return {
      pending: interventions.filter((record) => record.status === "pending"),
      approved: interventions.filter((record) => record.status === "approved"),
      rejected: interventions.filter((record) => record.status === "rejected"),
    } as const;
  }, [interventions]);

  async function reviewIntervention(recordId: string, nextStatus: "approved" | "rejected") {
    const notes = (qaNotesDraft[recordId] ?? "").trim();

    if (nextStatus === "approved" && !notes) {
      setQaErrors((previous) => ({
        ...previous,
        [recordId]: "QA notes are required before approving.",
      }));
      return;
    }

    setQaErrors((previous) => ({ ...previous, [recordId]: "" }));
    setQaSavingRecordId(recordId);

    const reviewedAt = new Date().toISOString();
    const payload = {
      status: nextStatus,
      qa_notes: notes || null,
      reviewed_at: reviewedAt,
    };

    const { error } = await supabase
      .from("interventions")
      .update(payload)
      .eq("id", recordId);

    if (error) {
      setQaErrors((previous) => ({
        ...previous,
        [recordId]: `Unable to update intervention: ${error.message}`,
      }));
      setQaSavingRecordId(null);
      return;
    }

    setInterventions((previous) =>
      previous.map((record) =>
        record.id === recordId
          ? {
              ...record,
              status: nextStatus,
              qaNotes: notes || null,
              reviewedAt,
            }
          : record,
      ),
    );

    setQaSavingRecordId(null);
  }

  async function exportInterventionPdf(record: InterventionRecord) {
    const response = await fetch("/api/interventions/pdf", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        intervention: {
          id: record.id,
          interventionAt: record.interventionAt,
          equipmentId: record.equipmentId,
          zone: record.zone,
          category: record.category,
          description: record.description,
          durationMinutes: record.durationMinutes,
          severityScore: record.severityScore,
          occurrenceScore: record.occurrenceScore,
          detectionScore: record.detectionScore,
          status: record.status,
          qaNotes: record.qaNotes,
          reviewedAt: record.reviewedAt,
          createdAt: new Date().toISOString(),
          companyThreshold: defaultThreshold,
        },
      }),
    });

    if (!response.ok) {
      return;
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = `intervention-${record.id}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
      <PortfolioWarningBanner />

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-bold">Annex 1 Intervention Risk Assessor</h1>
        <p className="mt-2 text-sm text-slate-700">
          Operator Logging Form + QA Dashboard (Portfolio Demo — Non-GMP)
        </p>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold">Log Intervention</h2>
        <form className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm font-medium text-slate-800">
            Datetime
            <input
              type="datetime-local"
              value={interventionAt}
              onChange={(event) => setInterventionAt(event.target.value)}
              className="rounded-md border border-slate-300 px-3 py-2"
              required
            />
          </label>

          <label className="flex flex-col gap-1 text-sm font-medium text-slate-800">
            Equipment ID
            <input
              type="text"
              value={equipmentId}
              onChange={(event) => setEquipmentId(event.target.value)}
              className="rounded-md border border-slate-300 px-3 py-2"
              placeholder="e.g. FILL-LN-01"
              required
            />
          </label>

          <label className="flex flex-col gap-1 text-sm font-medium text-slate-800">
            Zone
            <select
              value={zone}
              onChange={(event) => setZone(event.target.value as Zone)}
              className="rounded-md border border-slate-300 px-3 py-2"
            >
              {zones.map((zoneOption) => (
                <option key={zoneOption} value={zoneOption}>
                  {zoneOption}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-sm font-medium text-slate-800">
            Category
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value as Category)}
              className="rounded-md border border-slate-300 px-3 py-2"
            >
              {categories.map((categoryOption) => (
                <option key={categoryOption} value={categoryOption}>
                  {categoryOption}
                </option>
              ))}
            </select>
          </label>

          <label className="md:col-span-2 flex flex-col gap-1 text-sm font-medium text-slate-800">
            Description
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className="min-h-28 rounded-md border border-slate-300 px-3 py-2"
              placeholder="Describe the aseptic intervention"
              required
            />
          </label>

          <label className="flex flex-col gap-1 text-sm font-medium text-slate-800">
            Duration (minutes)
            <input
              type="number"
              min={1}
              value={durationMinutes}
              onChange={(event) =>
                setDurationMinutes(
                  event.target.value === "" ? "" : Number(event.target.value),
                )
              }
              className="rounded-md border border-slate-300 px-3 py-2"
              required
            />
          </label>

          <div className="md:col-span-2 mt-2 grid grid-cols-1 gap-4 rounded-md border border-slate-200 bg-slate-50 p-4 md:grid-cols-3">
            <label className="flex flex-col gap-1 text-sm font-medium text-slate-800">
              Severity (S)
              <select
                value={severityScore}
                onChange={(event) => setSeverityScore(Number(event.target.value))}
                className="rounded-md border border-slate-300 px-3 py-2"
              >
                {scores.map((score) => (
                  <option key={score} value={score}>
                    {score}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-sm font-medium text-slate-800">
              Occurrence (O)
              <select
                value={occurrenceScore}
                onChange={(event) => setOccurrenceScore(Number(event.target.value))}
                className="rounded-md border border-slate-300 px-3 py-2"
              >
                {scores.map((score) => (
                  <option key={score} value={score}>
                    {score}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-sm font-medium text-slate-800">
              Detection (D)
              <select
                value={detectionScore}
                onChange={(event) => setDetectionScore(Number(event.target.value))}
                className="rounded-md border border-slate-300 px-3 py-2"
              >
                {scores.map((score) => (
                  <option key={score} value={score}>
                    {score}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="md:col-span-2 flex flex-wrap items-center gap-3 rounded-md border border-slate-300 bg-white p-4">
            <span className="text-sm font-medium text-slate-700">Live RPN:</span>
            <span className="rounded bg-slate-900 px-3 py-1 text-sm font-bold text-white">
              {rpnScore}
            </span>
            <span
              className={`rounded px-3 py-1 text-xs font-bold ${
                isHighRisk
                  ? "border border-red-300 bg-red-100 text-red-800"
                  : "border border-emerald-300 bg-emerald-100 text-emerald-800"
              }`}
            >
              {isHighRisk
                ? `High Risk (>${defaultThreshold})`
                : `Within Threshold (≤${defaultThreshold})`}
            </span>
          </div>

          <div className="md:col-span-2">
            <button
              type="button"
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              disabled={
                !interventionAt ||
                !equipmentId.trim() ||
                !description.trim() ||
                durationMinutes === ""
              }
            >
              Save Intervention (Step 3 UI)
            </button>
          </div>
        </form>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-xl font-semibold">QA Dashboard</h2>
          <div className="inline-flex rounded-md border border-slate-300 p-1 text-sm">
            <button
              type="button"
              className={`rounded px-3 py-1 font-medium ${
                viewMode === "kanban" ? "bg-slate-900 text-white" : "text-slate-700"
              }`}
              onClick={() => setViewMode("kanban")}
            >
              Kanban View
            </button>
            <button
              type="button"
              className={`rounded px-3 py-1 font-medium ${
                viewMode === "list" ? "bg-slate-900 text-white" : "text-slate-700"
              }`}
              onClick={() => setViewMode("list")}
            >
              List View
            </button>
          </div>
        </div>

        <p className="mt-2 text-sm text-slate-600">
          QA approvals/rejections update <code>interventions.status</code>, <code>qa_notes</code>, and <code>reviewed_at</code>. This is intentionally wired to database update operations so your Supabase status-change trigger can create immutable Annex 11 audit log rows.
        </p>

        {viewMode === "kanban" ? (
          <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-3">
            {qaStatuses.map((status) => (
              <div key={status} className="rounded-md border border-slate-200 bg-slate-50 p-4">
                <h3 className="text-sm font-bold uppercase tracking-wide text-slate-700">
                  {status}
                </h3>
                <div className="mt-3 flex flex-col gap-3">
                  {groupedInterventions[status].map((record) => {
                    const rpn = rpnForRecord(record);
                    const highRisk = rpn > defaultThreshold;

                    return (
                      <article key={record.id} className="rounded-md border border-slate-200 bg-white p-3">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm font-semibold text-slate-900">{record.equipmentId}</p>
                          <span className="rounded bg-slate-900 px-2 py-0.5 text-xs font-bold text-white">
                            RPN {rpn}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-slate-600">{record.zone} · {record.category}</p>
                        <p className="mt-2 text-xs text-slate-700">{record.description}</p>

                        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                          <span
                            className={`rounded border px-2 py-0.5 font-semibold ${
                              highRisk
                                ? "border-red-300 bg-red-100 text-red-700"
                                : "border-emerald-300 bg-emerald-100 text-emerald-700"
                            }`}
                          >
                            {highRisk ? "High Risk" : "Within Threshold"}
                          </span>
                          {record.reviewedAt ? (
                            <span className="text-slate-500">
                              Reviewed: {new Date(record.reviewedAt).toLocaleString()}
                            </span>
                          ) : null}
                        </div>

                        {status === "pending" ? (
                          <div className="mt-3 space-y-2">
                            <label className="flex flex-col gap-1 text-xs font-medium text-slate-700">
                              QA Notes (required for approval)
                              <textarea
                                value={qaNotesDraft[record.id] ?? ""}
                                onChange={(event) =>
                                  setQaNotesDraft((previous) => ({
                                    ...previous,
                                    [record.id]: event.target.value,
                                  }))
                                }
                                className="min-h-20 rounded-md border border-slate-300 px-2 py-1"
                                placeholder="Enter QA decision rationale"
                              />
                            </label>

                            {qaErrors[record.id] ? (
                              <p className="text-xs font-medium text-red-700">{qaErrors[record.id]}</p>
                            ) : null}

                            <div className="flex gap-2">
                              <button
                                type="button"
                                className="rounded-md bg-emerald-700 px-2 py-1 text-xs font-semibold text-white disabled:opacity-60"
                                onClick={() => void reviewIntervention(record.id, "approved")}
                                disabled={qaSavingRecordId === record.id}
                              >
                                Approve
                              </button>
                              <button
                                type="button"
                                className="rounded-md bg-red-700 px-2 py-1 text-xs font-semibold text-white disabled:opacity-60"
                                onClick={() => void reviewIntervention(record.id, "rejected")}
                                disabled={qaSavingRecordId === record.id}
                              >
                                Reject
                              </button>
                              <button
                                type="button"
                                className="rounded-md bg-slate-700 px-2 py-1 text-xs font-semibold text-white"
                                onClick={() => void exportInterventionPdf(record)}
                              >
                                Export PDF
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="mt-2 flex flex-wrap items-center gap-2">
                            <p className="text-xs text-slate-700">
                              QA Notes: {record.qaNotes ?? "N/A"}
                            </p>
                            <button
                              type="button"
                              className="rounded-md bg-slate-700 px-2 py-1 text-xs font-semibold text-white"
                              onClick={() => void exportInterventionPdf(record)}
                            >
                              Export PDF
                            </button>
                          </div>
                        )}
                      </article>
                    );
                  })}
                  {groupedInterventions[status].length === 0 ? (
                    <p className="rounded-md border border-dashed border-slate-300 bg-white p-3 text-xs text-slate-500">
                      No interventions in this status.
                    </p>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-5 overflow-auto rounded-md border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold text-slate-700">Equipment</th>
                  <th className="px-3 py-2 text-left font-semibold text-slate-700">Zone</th>
                  <th className="px-3 py-2 text-left font-semibold text-slate-700">Status</th>
                  <th className="px-3 py-2 text-left font-semibold text-slate-700">RPN</th>
                  <th className="px-3 py-2 text-left font-semibold text-slate-700">Reviewed At</th>
                  <th className="px-3 py-2 text-left font-semibold text-slate-700">Export</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {interventions.map((record) => (
                  <tr key={record.id}>
                    <td className="px-3 py-2">{record.equipmentId}</td>
                    <td className="px-3 py-2">{record.zone}</td>
                    <td className="px-3 py-2 capitalize">{record.status}</td>
                    <td className="px-3 py-2">{rpnForRecord(record)}</td>
                    <td className="px-3 py-2">
                      {record.reviewedAt ? new Date(record.reviewedAt).toLocaleString() : "-"}
                    </td>
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        className="rounded-md bg-slate-700 px-2 py-1 text-xs font-semibold text-white"
                        onClick={() => void exportInterventionPdf(record)}
                      >
                        PDF
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
