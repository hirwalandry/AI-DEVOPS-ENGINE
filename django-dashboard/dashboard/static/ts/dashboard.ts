interface AuditLogPayload {
    project_id: string;
    repository_name: string;
    target_language: "python" | "javascript";
    execution_status: "SUCCESS" | "FAILED" | "PENDING";
    execution_summary: string;
    created_at: string;
}

class DashboardTelemetryController {
    private apiEndpoint: string = "/api/v1/logs-stream/";
    private gridElement: HTMLElement | null;

    constructor() {
        this.gridElement = document.getElementById("logs-grid");
    }

    public async initializePollingLoop(): Promise<void> {
        await this.fetchLatestTelemetryLogs();
        setInterval(async () => {
            await this.fetchLatestTelemetryLogs();
        }, 4000);
    }

    private async fetchLatestTelemetryLogs(): Promise<void> {
        try {
            const response = await fetch(this.apiEndpoint);
            if (!response.ok) throw new Error("Network connectivity degradation detected.");

            const logsList: AuditLogPayload[] = await response.json();
            this.renderTelemetryCards(logsList);
        } catch (error) {
            console.error("Telemetry pipeline execution error:", error);
        }
    }

    private renderTelemetryCards(logs: AuditLogPayload[]): void {
        if (!this.gridElement) return;

        if (logs.length === 0) {
            this.gridElement.innerHTML = `
                <div class="col-span-full text-center py-12 text-slate-500 border border-dashed border-slate-800 rounded-xl">
                    No active automation traces recorded in this cycle.
                </div>`;
            return;
        }

        this.gridElement.innerHTML = "";

        logs.forEach((log) => {
            const cardHtml = this.createCardElementStructure(log);
            this.gridElement!.appendChild(cardHtml);
        });
    }

    private createCardElementStructure(log: AuditLogPayload): HTMLElement {
        const cardWrapper = document.createElement("div");
        cardWrapper.className = "flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur transition-all duration-300 hover:border-slate-700 hover:bg-slate-900/60";

        const isSuccess = log.execution_status === "SUCCESS";
        const isPending = log.execution_status === "PENDING";

        const statusBadgeStyle = isSuccess
            ? "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20"
            : isPending
                ? "bg-amber-500/10 text-amber-400 ring-amber-500/20 animate-pulse"
                : "bg-rose-500/10 text-rose-400 ring-rose-500/20";

        const languageBadgeStyle = log.target_language === "python"
            ? "bg-blue-500/10 text-blue-400 ring-blue-500/20"
            : "bg-yellow-500/10 text-yellow-400 ring-yellow-500/20";

        cardWrapper.innerHTML = `
            <div>
                <div class="flex items-center justify-between gap-x-4">
                    <h3 class="text-sm font-semibold leading-6 text-white truncate max-w-[180px]" title="${log.repository_name}">
                        ${log.repository_name}
                    </h3>
                    <span class="rounded-full px-2 py-1 text-xs font-medium ring-1 ring-inset ${statusBadgeStyle}">
                        ${log.execution_status}
                    </span>
                </div>
                <div class="mt-1 flex items-center gap-x-2 text-xs text-slate-500">
                    <span>ID: ${log.project_id}</span>
                    <span>•</span>
                    <span class="rounded px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider ring-1 ring-inset ${languageBadgeStyle}">
                        ${log.target_language}
                    </span>
                </div>
                <div class="mt-4 rounded bg-slate-950/80 p-3 border border-slate-900">
                    <p class="font-mono text-xs text-slate-400 leading-relaxed line-clamp-4 overflow-hidden whitespace-pre-wrap">
                        ${log.execution_summary}
                    </p>
                </div>
            </div>
            <div class="mt-6 border-t border-slate-800/60 pt-4 flex items-center justify-between text-[11px] text-slate-500">
                <span>Timestamp Matrix</span>
                <span class="font-mono">${new Date(log.created_at).toLocaleTimeString()}</span>
            </div>
        `;

        return cardWrapper;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const controller = new DashboardTelemetryController();
    controller.initializePollingLoop();
});
