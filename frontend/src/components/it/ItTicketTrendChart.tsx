interface TicketTrendWeek {
  week_start: string;
  opened_count: number;
  closed_count: number;
}

interface ItTicketTrendChartProps {
  loading: boolean;
  error: string;
  ticketTrend: TicketTrendWeek[];
}

const openedBarColor = "#D1353B";
const closedBarColor = "#D48A6B";

const formatTrendWeekLabel = (weekStart: string): string => {
  const parsed = new Date(weekStart);
  if (Number.isNaN(parsed.getTime())) {
    return "W1";
  }

  const month = parsed.toLocaleDateString(undefined, { month: "short" });
  const weekOfMonth = Math.min(4, Math.ceil(parsed.getDate() / 7));

  return `W${weekOfMonth} ${month}`.trim();
};

const ItTicketTrendChart = ({ loading, error, ticketTrend }: ItTicketTrendChartProps) => {
  const maxTrendValue = ticketTrend.length
    ? Math.max(...ticketTrend.map((week) => Math.max(week.opened_count, week.closed_count)), 1)
    : 1;

  const trendAxisMax = Math.max(4, Math.ceil(maxTrendValue / 4) * 4);
  const quarter = trendAxisMax / 4;
  const trendAxisTicks = [quarter, quarter * 2, quarter * 3, trendAxisMax].map((tick) => Math.round(tick));

  return (
    <section className="bg-white border border-gray-200 rounded-lg p-4 md:p-5 shadow-sm">
      <div className="flex flex-col gap-2 mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Tickets Opened vs Closed (Weekly)</h2>
        <p className="text-sm text-gray-500">Opened vs closed tickets for the last 6 weeks.</p>
      </div>

      {loading ? (
        <div className="text-sm text-gray-500">Loading throughput chart...</div>
      ) : error ? (
        <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md p-3">{error}</div>
      ) : (
        <div className="space-y-4">
          <div className="overflow-x-auto">
            <div className="min-w-[760px] flex items-end gap-4">
              <div className="w-16 h-72 pb-3 flex flex-col justify-between text-right text-[11px] text-gray-500">
                <div />
                {trendAxisTicks.slice().reverse().map((tick) => (
                  <div key={tick} className="h-0 flex items-center justify-end gap-2">
                    <span>{tick}</span>
                    <span className="inline-block h-px w-4 bg-gray-300" />
                  </div>
                ))}
              </div>

              <div className="flex-1">
                <div className="relative h-72 pb-3">
                  <div className="absolute inset-x-0 top-0 bottom-3 pointer-events-none">
                    {trendAxisTicks.map((tick) => {
                      const tickBottom = Math.max((tick / trendAxisMax) * 100, 0);

                      return (
                        <div
                          key={tick}
                          className="absolute left-0 right-0 border-t border-dashed border-gray-200"
                          style={{ bottom: `${tickBottom}%` }}
                        />
                      );
                    })}
                  </div>

                  <div className="relative flex items-end gap-3 h-full">
                    {ticketTrend.map((week) => {
                      const openedHeight = Math.max((week.opened_count / trendAxisMax) * 100, 3);
                      const closedHeight = Math.max((week.closed_count / trendAxisMax) * 100, 3);

                      return (
                        <div key={week.week_start} className="flex-1 flex flex-col items-center justify-end h-full min-w-0">
                          <div className="w-full flex items-end justify-center gap-2 flex-1 px-1">
                            <div className="flex flex-col items-center justify-end gap-1 h-full w-1/2">
                              <span className="text-[11px] text-gray-500">{week.opened_count}</span>
                              <div className="w-full max-w-9 h-full flex items-end justify-center">
                                <div
                                  className="w-full rounded-t-md shadow-sm"
                                  style={{
                                    height: `${openedHeight}%`,
                                    backgroundColor: openedBarColor,
                                  }}
                                />
                              </div>
                            </div>

                            <div className="flex flex-col items-center justify-end gap-1 h-full w-1/2">
                              <span className="text-[11px] text-gray-500">{week.closed_count}</span>
                              <div className="w-full max-w-9 h-full flex items-end justify-center">
                                <div
                                  className="w-full rounded-t-md shadow-sm"
                                  style={{
                                    height: `${closedHeight}%`,
                                    backgroundColor: closedBarColor,
                                  }}
                                />
                              </div>
                            </div>
                          </div>

                          <div className="mt-2 text-[11px] text-gray-500 text-center leading-tight">
                            {formatTrendWeekLabel(week.week_start)}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center gap-6 text-xs font-medium text-gray-600">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: openedBarColor }} />
              <span>Opened</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: closedBarColor }} />
              <span>Closed</span>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default ItTicketTrendChart;
