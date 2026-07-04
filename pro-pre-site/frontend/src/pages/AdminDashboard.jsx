import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api, API } from "@/lib/api";
import {
  LogOut,
  ShieldAlert,
  Calendar,
  ListChecks,
  Loader2,
  Check,
  X,
  Mail,
  Phone,
  MapPin,
  Users,
  Image as ImageIcon,
  Upload,
  Eye,
  EyeOff,
  Trash2,
  FileText,
  TrendingUp,
  Euro,
  Percent,
  Download,
  Camera,
  Clock,
  Workflow,
  UserCheck,
  History,
  AlertTriangle,
  CalendarClock,
  Zap,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import ContractManagerModal from "@/components/admin/ContractManagerModal";

const STATUS_COLOR = {
  nouvelle: "bg-blue-100 text-blue-700",
  confirmee: "bg-amber-100 text-amber-700",
  completee: "bg-emerald-100 text-emerald-700",
  annulee: "bg-slate-200 text-slate-600",
};

const CONTRACT_STATUS_COLOR = {
  signed: "bg-blue-100 text-blue-700",
  test_done: "bg-emerald-100 text-emerald-700",
  completed: "bg-emerald-100 text-emerald-700",
  cancelled: "bg-slate-100 text-slate-500",
};

const DEPOSIT_LABELS = {
  none: "—",
  revolut: "Revolut",
  bonifico: "Bonifico",
  in_person: "En personne",
};

export default function AdminDashboard() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = React.useState(location.state?.user || null);
  const [loading, setLoading] = React.useState(!location.state?.user);
  const [bookings, setBookings] = React.useState([]);
  const [contracts, setContracts] = React.useState([]);
  const [kpi, setKpi] = React.useState(null);
  const [clients, setClients] = React.useState([]);
  const [gallery, setGallery] = React.useState([]);

  React.useEffect(() => {
    if (window.location.hash?.includes("session_id=")) return;
    if (location.state?.user) return;
    api
      .get("/auth/me")
      .then((r) => setUser(r.data))
      .catch(() => navigate("/login", { replace: true }))
      .finally(() => setLoading(false));
  }, [navigate, location.state]);

  const loadAll = React.useCallback(() => {
    if (!user?.is_admin) return;
    Promise.all([
      api.get("/admin/bookings"),
      api.get("/admin/kpi"),
      api.get("/admin/clients"),
      api.get("/admin/gallery"),
      api.get("/admin/contracts"),
    ])
      .then(([b, k, c, g, ct]) => {
        setBookings(b.data.bookings);
        setKpi(k.data);
        setClients(c.data.clients);
        setGallery(g.data.items);
        setContracts(ct.data.contracts);
      })
      .catch(() => {});
  }, [user]);

  React.useEffect(() => {
    loadAll();
  }, [loadAll]);

  const reloadGallery = () => api.get("/admin/gallery").then((g) => setGallery(g.data.items));
  const reloadContracts = () => api.get("/admin/contracts").then((r) => setContracts(r.data.contracts));

  const logout = async () => {
    await api.post("/auth/logout").catch(() => {});
    navigate("/login", { replace: true });
  };

  const updateStatus = async (id, status) => {
    try {
      await api.patch(`/admin/bookings/${id}`, { status });
      setBookings(bookings.map((b) => (b.id === id ? { ...b, status } : b)));
      toast.success(t("admin.status_updated"));
      loadAll();
    } catch {
      toast.error(t("admin.error"));
    }
  };

  if (loading)
    return (
      <div className="section">
        <div className="container-narrow">
          <Loader2 className="h-6 w-6 animate-spin" />
        </div>
      </div>
    );

  if (user && !user.is_admin) {
    return (
      <div className="section">
        <div className="container-narrow max-w-md text-center" data-testid="access-denied">
          <ShieldAlert className="mx-auto h-12 w-12 text-red-500" />
          <h2 className="mt-4 text-2xl font-semibold text-navy">{t("admin.access_denied")}</h2>
          <p className="mt-2 text-slate-600">{t("admin.access_denied_body")}</p>
          <button onClick={() => navigate("/mon-espace")} className="btn-primary mt-6">
            Mon espace
          </button>
          <button onClick={logout} className="btn-outline mt-3">
            {t("nav.logout")}
          </button>
        </div>
      </div>
    );
  }

  // Weekly calendar grouping
  const today = new Date();
  const weekStart = new Date(today);
  weekStart.setDate(today.getDate() - today.getDay() + 1);
  const week = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart);
    d.setDate(weekStart.getDate() + i);
    return d;
  });
  const fmt = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const dayLabel = (d) => d.toLocaleDateString(undefined, { weekday: "short", day: "2-digit", month: "short" });

  return (
    <div className="section">
      <div className="container-narrow">
        <div className="flex items-center justify-between flex-wrap gap-3" data-testid="admin-header">
          <div>
            <h1 className="text-3xl font-semibold text-navy">{t("admin.title")}</h1>
            <p className="text-sm text-slate-500">{user?.email}</p>
          </div>
          <div className="flex gap-2">
            <a
              href={`${API}/admin/backup-download?fmt=zip`}
              className="btn-outline"
              data-testid="admin-backup-download"
              title="Télécharger le backup complet (frontend + backend + database) au format ZIP"
            >
              <Download className="h-4 w-4" />
              Backup .zip
            </a>
            <button onClick={logout} className="btn-outline" data-testid="admin-logout">
              <LogOut className="h-4 w-4" />
              {t("nav.logout")}
            </button>
          </div>
        </div>

        {kpi && <KpiRow kpi={kpi} />}

        <Tabs defaultValue="list" className="mt-8" data-testid="admin-tabs">
          <TabsList className="flex-wrap h-auto">
            <TabsTrigger value="list" data-testid="tab-list">
              <ListChecks className="h-4 w-4 mr-2" />
              {t("admin.bookings")}
            </TabsTrigger>
            <TabsTrigger value="contracts" data-testid="tab-contracts">
              <FileText className="h-4 w-4 mr-2" />
              {t("admin.contracts")}
            </TabsTrigger>
            <TabsTrigger value="pipeline" data-testid="tab-pipeline">
              <Workflow className="h-4 w-4 mr-2" />
              {t("admin.pipeline.tab")}
            </TabsTrigger>
            <TabsTrigger value="calendar" data-testid="tab-calendar">
              <Calendar className="h-4 w-4 mr-2" />
              {t("admin.calendar")}
            </TabsTrigger>
            <TabsTrigger value="clients" data-testid="tab-clients">
              <Users className="h-4 w-4 mr-2" />
              {t("admin.clients")}
            </TabsTrigger>
            <TabsTrigger value="gallery" data-testid="tab-gallery">
              <ImageIcon className="h-4 w-4 mr-2" />
              {t("admin.gallery")}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="list">
            {bookings.length === 0 ? (
              <p className="text-slate-500 py-8" data-testid="no-bookings">
                {t("admin.no_bookings")}
              </p>
            ) : (
              <div className="mt-4 grid gap-3">
                {bookings.map((b) => (
                  <div key={b.id} className="card-clean p-5" data-testid={`booking-row-${b.id}`}>
                    <div className="flex flex-wrap justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-navy">{b.full_name}</p>
                          <Badge className={STATUS_COLOR[b.status] || "bg-slate-100"}>
                            {t(`admin.status.${b.status}`)}
                          </Badge>
                          {b.type === "defi" && <Badge className="bg-[#5BA4D4]/15 text-[#5BA4D4]">Défi</Badge>}
                        </div>
                        <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-600">
                          <a href={`tel:${b.phone}`} className="flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {b.phone}
                          </a>
                          <a href={`mailto:${b.email}`} className="flex items-center gap-1">
                            <Mail className="h-3 w-3" />
                            {b.email}
                          </a>
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {b.address}, {b.postal_code} {b.city}
                          </span>
                        </div>
                        <div className="mt-2 text-sm">
                          <span className="font-medium">{b.date}</span> · {b.time_slot}
                          {b.estimated_price > 0 && (
                            <span className="ml-3 text-[#5BA4D4] font-semibold">€{b.estimated_price}</span>
                          )}
                        </div>
                        {b.items?.length > 0 && (
                          <p className="mt-1 text-xs text-slate-500">
                            {b.items
                              .map(
                                (it) =>
                                  `${t(`services.items.${it.service_id}.name`, it.service_id)}${
                                    it.quantity > 1 ? ` ×${it.quantity}` : ""
                                  }`,
                              )
                              .join(", ")}
                          </p>
                        )}
                        {b.notes && (
                          <p className="mt-1 text-xs text-slate-500 italic">&ldquo;{b.notes}&rdquo;</p>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {b.status === "nouvelle" && (
                          <button
                            onClick={() => updateStatus(b.id, "confirmee")}
                            className="text-xs rounded-lg bg-amber-100 text-amber-700 px-3 py-1.5 font-medium"
                            data-testid={`confirm-${b.id}`}
                          >
                            {t("admin.status.confirmee")}
                          </button>
                        )}
                        {(b.status === "nouvelle" || b.status === "confirmee") && (
                          <button
                            onClick={() => updateStatus(b.id, "completee")}
                            className="text-xs rounded-lg bg-emerald-100 text-emerald-700 px-3 py-1.5 font-medium flex items-center gap-1"
                            data-testid={`complete-${b.id}`}
                          >
                            <Check className="h-3 w-3" />
                            {t("admin.status.completee")}
                          </button>
                        )}
                        {b.status !== "annulee" && b.status !== "completee" && (
                          <button
                            onClick={() => updateStatus(b.id, "annulee")}
                            className="text-xs rounded-lg bg-slate-100 text-slate-600 px-3 py-1.5 font-medium flex items-center gap-1"
                            data-testid={`cancel-${b.id}`}
                          >
                            <X className="h-3 w-3" />
                            {t("admin.status.annulee")}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="contracts">
            <ContractsTab contracts={contracts} reload={reloadContracts} />
          </TabsContent>

          <TabsContent value="pipeline">
            <PipelineTab contracts={contracts} bookings={bookings} reload={reloadContracts} />
          </TabsContent>

          <TabsContent value="calendar">
            <div className="mt-4 grid grid-cols-1 md:grid-cols-7 gap-3" data-testid="weekly-calendar">
              {week.map((d) => {
                const key = fmt(d);
                const dayBookings = bookings.filter((b) => b.date === key && b.status !== "annulee");
                return (
                  <div key={key} className="card-clean p-3 min-h-[160px]">
                    <p className="text-xs font-semibold text-navy">{dayLabel(d)}</p>
                    <div className="mt-2 space-y-1">
                      {dayBookings.length === 0 && <p className="text-xs text-slate-400">—</p>}
                      {dayBookings.map((b) => (
                        <div key={b.id} className="rounded-lg bg-[#5BA4D4]/10 px-2 py-1 text-xs">
                          <p className="font-medium text-navy">{b.time_slot}</p>
                          <p className="text-slate-600 truncate">{b.full_name}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </TabsContent>

          <TabsContent value="clients">
            <ClientsTab clients={clients} />
          </TabsContent>

          <TabsContent value="gallery">
            <GalleryTab items={gallery} reload={reloadGallery} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function KpiRow({ kpi }) {
  const { t } = useTranslation();
  return (
    <div className="mt-8 space-y-4" data-testid="admin-kpi">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          icon={<ListChecks className="h-5 w-5" />}
          label={t("admin.kpi.total_bookings")}
          value={kpi.total_bookings}
          hint={`${kpi.last_30_days.bookings} ${t("admin.kpi.last_30d")}`}
          color="text-[#5BA4D4]"
          testid="kpi-total"
        />
        <KpiCard
          icon={<Euro className="h-5 w-5" />}
          label={t("admin.kpi.revenue_completed")}
          value={`€${Math.round(kpi.revenue.completed)}`}
          hint={`€${Math.round(kpi.revenue.confirmed)} ${t("admin.kpi.confirmed")}`}
          color="text-emerald-600"
          testid="kpi-revenue"
        />
        <KpiCard
          icon={<Percent className="h-5 w-5" />}
          label={t("admin.kpi.conversion_rate")}
          value={`${kpi.conversion_rate_percent}%`}
          hint={`${kpi.contracts.total} ${t("admin.kpi.contracts_total")}`}
          color="text-purple-600"
          testid="kpi-conversion"
        />
        <KpiCard
          icon={<TrendingUp className="h-5 w-5" />}
          label={t("admin.kpi.avg_ticket")}
          value={`€${Math.round(kpi.clients.avg_ticket_completed)}`}
          hint={`${kpi.clients.unique} ${t("admin.kpi.unique_clients")}`}
          color="text-amber-600"
          testid="kpi-avg-ticket"
        />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MiniStat label={t("admin.status.nouvelle")} value={kpi.by_status.nouvelle} color="bg-blue-100 text-blue-700" />
        <MiniStat label={t("admin.status.confirmee")} value={kpi.by_status.confirmee} color="bg-amber-100 text-amber-700" />
        <MiniStat label={t("admin.status.completee")} value={kpi.by_status.completee} color="bg-emerald-100 text-emerald-700" />
        <MiniStat label={t("admin.status.annulee")} value={kpi.by_status.annulee} color="bg-slate-200 text-slate-600" />
      </div>

      {kpi.top_services.length > 0 && (
        <div className="card-clean p-5">
          <p className="text-xs uppercase tracking-wider font-semibold text-[#5BA4D4] mb-3">
            {t("admin.kpi.top_services")}
          </p>
          <div className="space-y-2">
            {kpi.top_services.map((s) => (
              <div key={s.id} className="flex items-center gap-3" data-testid={`top-service-${s.id}`}>
                <span className="text-sm text-navy w-40 truncate">{s.label}</span>
                <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#5BA4D4]"
                    style={{ width: `${(s.count / kpi.top_services[0].count) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-semibold text-navy w-8 text-right">{s.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function KpiCard({ icon, label, value, hint, color, testid }) {
  return (
    <div className="card-clean p-5" data-testid={testid}>
      <div className={`inline-flex h-9 w-9 items-center justify-center rounded-lg bg-slate-50 ${color}`}>
        {icon}
      </div>
      <p className="mt-3 text-xs uppercase tracking-wider font-semibold text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-navy">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

function MiniStat({ label, value, color }) {
  return (
    <div className={`rounded-xl px-4 py-3 flex justify-between items-center ${color}`}>
      <span className="text-sm font-medium">{label}</span>
      <span className="text-lg font-bold">{value}</span>
    </div>
  );
}

function ContractsTab({ contracts, reload }) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = React.useState(null);
  const [uploading, setUploading] = React.useState({});
  const [deleting, setDeleting] = React.useState({});
  const [manageContract, setManageContract] = React.useState(null);

  const uploadAfterPhoto = async (contractId, file) => {
    if (!file) return;
    if (file.size > 15 * 1024 * 1024) {
      toast.error(t("admin.error"));
      return;
    }
    setUploading((u) => ({ ...u, [contractId]: true }));
    try {
      const b64 = await resizeImageToB64(file);
      await api.post(`/admin/contracts/${contractId}/after-photo`, {
        photo_after_base64: b64,
      });
      toast.success(t("admin.contracts_ui.after_uploaded"));
      reload();
    } catch {
      toast.error(t("admin.error"));
    } finally {
      setUploading((u) => ({ ...u, [contractId]: false }));
    }
  };

  const del = async (contractId) => {
    if (!window.confirm(t("admin.contracts_ui.confirm_delete"))) return;
    setDeleting((d) => ({ ...d, [contractId]: true }));
    try {
      await api.delete(`/admin/contracts/${contractId}`);
      toast.success(t("admin.contracts_ui.deleted"));
      reload();
    } catch {
      toast.error(t("admin.error"));
    } finally {
      setDeleting((d) => ({ ...d, [contractId]: false }));
    }
  };

  const updateStatus = async (id, updates) => {
    try {
      await api.patch(`/admin/contracts/${id}`, updates);
      toast.success(t("admin.status_updated"));
      reload();
    } catch {
      toast.error(t("admin.error"));
    }
  };

  if (contracts.length === 0) {
    return (
      <p className="mt-6 text-slate-500" data-testid="no-contracts">
        {t("admin.contracts_ui.empty")}
      </p>
    );
  }

  return (
    <div className="mt-6 grid gap-4" data-testid="contracts-tab">
      {contracts.map((c) => (
        <div key={c.id} className="card-clean p-5" data-testid={`contract-row-${c.id}`}>
          <div className="flex flex-wrap justify-between items-start gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <p className="font-semibold text-navy">{c.client_name}</p>
                <Badge className={CONTRACT_STATUS_COLOR[c.status] || "bg-slate-100"}>
                  {t(`me.status.${c.status}`)}
                </Badge>
                <span className="text-xs text-slate-400">
                  {t("me.ref")}: {c.id.slice(0, 8).toUpperCase()}
                </span>
              </div>
              <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-600">
                <a href={`tel:${c.client_phone}`} className="flex items-center gap-1">
                  <Phone className="h-3 w-3" />
                  {c.client_phone}
                </a>
                <a href={`mailto:${c.client_email}`} className="flex items-center gap-1">
                  <Mail className="h-3 w-3" />
                  {c.client_email}
                </a>
                <span className="flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {c.address}, {c.postal_code} {c.city}
                </span>
              </div>
              <div className="mt-2 text-sm">
                <span className="font-medium">{c.date}</span> · {c.time_slot} ·{" "}
                <span className="text-[#5BA4D4] font-semibold">
                  {c.service_label} — €{c.service_price}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-500 italic">&ldquo;{c.dirty_area_description}&rdquo;</p>
              <div className="mt-2 flex items-center gap-3 text-xs">
                <span className="rounded bg-slate-100 px-2 py-0.5">
                  {t("admin.contracts_ui.deposit")}: {DEPOSIT_LABELS[c.deposit_choice] || c.deposit_choice} ·{" "}
                  <b>{c.deposit_status}</b>
                </span>
                {c.has_photo_before ? (
                  <span className="text-slate-500 flex items-center gap-1">
                    <ImageIcon className="h-3 w-3" /> {t("me.photo_before")}
                  </span>
                ) : null}
                {c.has_photo_after ? (
                  <span className="text-emerald-600 flex items-center gap-1">
                    <Check className="h-3 w-3" /> {t("me.photo_after")}
                  </span>
                ) : (
                  <span className="text-amber-600 flex items-center gap-1">
                    <Clock className="h-3 w-3" /> {t("me.photo_after_pending")}
                  </span>
                )}
              </div>
            </div>
            <div className="flex flex-col gap-2 items-end">
              <a
                href={`${API}/contracts/${c.id}/pdf`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs rounded-lg bg-slate-100 hover:bg-slate-200 px-3 py-1.5 font-medium flex items-center gap-1"
                data-testid={`contract-pdf-${c.id}`}
              >
                <Download className="h-3 w-3" /> PDF
              </a>
              <button
                onClick={() => setManageContract(c)}
                className="text-xs rounded-md bg-navy text-white hover:bg-navy/90 px-2 py-1 inline-flex items-center gap-1 font-medium"
                data-testid={`contract-tools-${c.id}`}
                title={t("admin.tools.manage")}
              >
                <Zap className="h-3 w-3" /> {t("admin.tools.manage")}
              </button>
              <button
                onClick={() => setExpanded(expanded === c.id ? null : c.id)}
                className="text-xs text-slate-500 hover:text-navy"
                data-testid={`contract-expand-${c.id}`}
              >
                {expanded === c.id ? t("admin.contracts_ui.hide") : t("admin.contracts_ui.manage")}
              </button>
            </div>
          </div>

          {expanded === c.id && (
            <div className="mt-4 pt-4 border-t border-slate-100 grid md:grid-cols-2 gap-4" data-testid={`contract-manage-${c.id}`}>
              <div>
                <p className="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-2">
                  {t("me.photo_before")}
                </p>
                {c.has_photo_before ? (
                  <AdminAuthImg
                    contractId={c.id}
                    kind="before"
                    testid={`contract-photo-before-${c.id}`}
                  />
                ) : (
                  <p className="text-xs text-slate-400 italic">{t("admin.contracts_ui.no_before")}</p>
                )}
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-2">
                  {t("me.photo_after")}
                </p>
                {c.has_photo_after ? (
                  <AdminAuthImg
                    contractId={c.id}
                    kind="after"
                    testid={`contract-photo-after-${c.id}`}
                  />
                ) : null}
                <label
                  className="mt-2 cursor-pointer inline-flex items-center gap-2 rounded-lg border border-dashed border-slate-300 hover:border-[#5BA4D4] px-3 py-2 text-xs w-full justify-center"
                  data-testid={`contract-upload-after-${c.id}`}
                >
                  <Camera className="h-3 w-3" />
                  {uploading[c.id] ? t("admin.contracts_ui.uploading") : t("admin.contracts_ui.upload_after")}
                  <input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    className="hidden"
                    onChange={(e) => uploadAfterPhoto(c.id, e.target.files?.[0])}
                  />
                </label>
              </div>

              <div className="md:col-span-2 flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
                <span className="text-xs font-semibold text-slate-500">{t("admin.contracts_ui.status")}:</span>
                {["signed", "test_done", "completed", "cancelled"].map((s) => (
                  <button
                    key={s}
                    disabled={c.status === s}
                    onClick={() => updateStatus(c.id, { status: s })}
                    className={`text-xs rounded-lg px-3 py-1.5 font-medium ${
                      c.status === s
                        ? "bg-navy text-white opacity-50"
                        : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                    }`}
                    data-testid={`contract-set-${s}-${c.id}`}
                  >
                    {t(`me.status.${s}`)}
                  </button>
                ))}
                {c.deposit_choice !== "none" && c.deposit_status !== "paid" && (
                  <button
                    onClick={() => updateStatus(c.id, { deposit_status: "paid" })}
                    className="text-xs rounded-lg bg-emerald-100 text-emerald-700 hover:bg-emerald-200 px-3 py-1.5 font-medium ml-2"
                    data-testid={`contract-mark-paid-${c.id}`}
                  >
                    <Check className="h-3 w-3 inline mr-1" />
                    {t("admin.contracts_ui.mark_deposit_paid")}
                  </button>
                )}
                <button
                  onClick={() => del(c.id)}
                  disabled={deleting[c.id]}
                  className="ml-auto text-xs rounded-lg bg-red-50 text-red-600 hover:bg-red-100 px-3 py-1.5 font-medium flex items-center gap-1"
                  data-testid={`contract-delete-${c.id}`}
                >
                  <Trash2 className="h-3 w-3" /> {t("admin.contracts_ui.delete")}
                </button>
              </div>
            </div>
          )}
        </div>
      ))}

      {manageContract ? (
        <ContractManagerModal
          contract={manageContract}
          onClose={() => setManageContract(null)}
          onChanged={reload}
        />
      ) : null}
    </div>
  );
}

function AdminAuthImg({ contractId, kind, testid }) {
  const [src, setSrc] = React.useState(null);
  React.useEffect(() => {
    let url;
    api
      .get(`/admin/contracts/${contractId}/photo/${kind}`, { responseType: "blob" })
      .then((r) => {
        url = URL.createObjectURL(r.data);
        setSrc(url);
      })
      .catch(() => {});
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [contractId, kind]);
  return (
    <div className="rounded-lg bg-slate-100 overflow-hidden aspect-video">
      {src ? <img src={src} alt="" className="w-full h-full object-cover" data-testid={testid} /> : null}
    </div>
  );
}

async function resizeImageToB64(file, maxDim = 1400, quality = 0.82) {
  const dataUrl = await new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = reject;
    r.readAsDataURL(file);
  });
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, maxDim / Math.max(img.width, img.height));
      const w = Math.round(img.width * scale);
      const h = Math.round(img.height * scale);
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, w, h);
      resolve(canvas.toDataURL("image/jpeg", quality));
    };
    img.onerror = () => resolve(dataUrl);
    img.src = dataUrl;
  });
}

function ClientsTab({ clients }) {
  const { t } = useTranslation();
  if (!clients?.length)
    return (
      <p className="mt-6 text-slate-500" data-testid="no-clients">
        {t("admin.no_clients")}
      </p>
    );
  return (
    <div className="mt-6 overflow-x-auto card-clean" data-testid="clients-table">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-slate-600 text-left">
          <tr>
            <th className="p-3 font-semibold">{t("admin.clients_ui.name")}</th>
            <th className="p-3 font-semibold">Email</th>
            <th className="p-3 font-semibold">{t("booking.phone")}</th>
            <th className="p-3 font-semibold">{t("booking.city")}</th>
            <th className="p-3 font-semibold text-right">{t("admin.clients_ui.bookings")}</th>
            <th className="p-3 font-semibold text-right">Total €</th>
            <th className="p-3 font-semibold">{t("admin.clients_ui.last_visit")}</th>
          </tr>
        </thead>
        <tbody>
          {clients.map((c, i) => (
            <tr key={c.email} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`client-row-${i}`}>
              <td className="p-3 font-medium text-navy">{c.full_name}</td>
              <td className="p-3">
                <a href={`mailto:${c.email}`} className="text-[#5BA4D4] hover:underline">
                  {c.email}
                </a>
              </td>
              <td className="p-3">
                <a href={`tel:${c.phone}`} className="text-slate-700 hover:text-[#1B2845]">
                  {c.phone}
                </a>
              </td>
              <td className="p-3 text-slate-600">
                {c.postal_code} {c.city}
              </td>
              <td className="p-3 text-right font-semibold">{c.bookings_count}</td>
              <td className="p-3 text-right text-[#5BA4D4] font-semibold">€{Math.round(c.total_spent)}</td>
              <td className="p-3 text-slate-500">{c.last_booking}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GalleryTab({ items, reload }) {
  const { t } = useTranslation();
  const [file, setFile] = React.useState(null);
  const [caption, setCaption] = React.useState("");
  const [category, setCategory] = React.useState("eau_extraite");
  const [uploading, setUploading] = React.useState(false);

  const upload = async () => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("caption", caption);
    fd.append("category", category);
    setUploading(true);
    try {
      await api.post("/admin/gallery", fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success(t("admin.gallery_ui.published"));
      setFile(null);
      setCaption("");
      reload();
    } catch {
      toast.error(t("admin.error"));
    } finally {
      setUploading(false);
    }
  };

  const togglePublish = async (item) => {
    await api.patch(`/admin/gallery/${item.id}`, { is_published: !item.is_published });
    reload();
  };

  const del = async (item) => {
    if (!window.confirm(t("admin.gallery_ui.confirm_delete"))) return;
    await api.delete(`/admin/gallery/${item.id}`);
    reload();
  };

  return (
    <div className="mt-6" data-testid="gallery-tab">
      <div className="card-clean p-5">
        <h3 className="font-semibold text-navy">{t("admin.gallery_ui.publish_new")}</h3>
        <p className="text-xs text-slate-500 mt-1">{t("admin.gallery_ui.publish_hint")}</p>
        <div className="mt-4 grid sm:grid-cols-2 gap-3">
          <label className="text-sm">
            <span className="font-medium">{t("admin.gallery_ui.category")}</span>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
              data-testid="gallery-category"
            >
              <option value="eau_extraite">{t("admin.gallery_ui.cat_eau")}</option>
              <option value="avant_apres">{t("admin.gallery_ui.cat_avant_apres")}</option>
              <option value="canape">{t("admin.gallery_ui.cat_canape")}</option>
              <option value="matelas">{t("admin.gallery_ui.cat_matelas")}</option>
              <option value="tapis">{t("admin.gallery_ui.cat_tapis")}</option>
              <option value="auto">{t("admin.gallery_ui.cat_auto")}</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="font-medium">{t("admin.gallery_ui.caption")}</span>
            <input
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
              placeholder={t("admin.gallery_ui.caption_placeholder")}
              data-testid="gallery-caption"
            />
          </label>
        </div>
        <div className="mt-4 flex items-center gap-3">
          <label
            className="cursor-pointer inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 hover:bg-slate-50 text-sm"
            data-testid="gallery-file-input"
          >
            <Upload className="h-4 w-4" /> {file ? file.name : t("admin.gallery_ui.choose_image")}
            <input type="file" accept="image/*" className="hidden" onChange={(e) => setFile(e.target.files?.[0])} />
          </label>
          <button
            onClick={upload}
            disabled={!file || uploading}
            className="btn-primary disabled:opacity-40"
            data-testid="gallery-upload-btn"
          >
            {uploading ? "…" : t("admin.gallery_ui.publish")}
          </button>
        </div>
      </div>

      <h3 className="mt-8 font-semibold text-navy">
        {t("admin.gallery_ui.published")} ({items.filter((i) => i.is_published).length}) ·{" "}
        {t("admin.gallery_ui.drafts")} ({items.filter((i) => !i.is_published).length})
      </h3>
      {items.length === 0 ? (
        <p className="mt-4 text-slate-500" data-testid="no-gallery">
          {t("admin.gallery_ui.empty")}
        </p>
      ) : (
        <div className="mt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {items.map((it) => (
            <div
              key={it.id}
              className={`card-clean overflow-hidden ${!it.is_published ? "opacity-60" : ""}`}
              data-testid={`gallery-item-${it.id}`}
            >
              <img src={`${API}/gallery/${it.storage_path}`} alt={it.caption} className="w-full h-40 object-cover" />
              <div className="p-3">
                <p className="text-xs text-slate-500 uppercase tracking-wide">{it.category}</p>
                <p className="text-sm text-navy font-medium mt-1 line-clamp-2">{it.caption || "—"}</p>
                <div className="mt-3 flex gap-2 text-xs">
                  <button
                    onClick={() => togglePublish(it)}
                    className="rounded-lg bg-slate-100 hover:bg-slate-200 px-2 py-1 flex items-center gap-1"
                    data-testid={`gallery-toggle-${it.id}`}
                  >
                    {it.is_published ? (
                      <>
                        <EyeOff className="h-3 w-3" />
                        {t("admin.gallery_ui.hide")}
                      </>
                    ) : (
                      <>
                        <Eye className="h-3 w-3" />
                        {t("admin.gallery_ui.publish")}
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => del(it)}
                    className="rounded-lg bg-red-50 text-red-600 hover:bg-red-100 px-2 py-1 flex items-center gap-1"
                    data-testid={`gallery-delete-${it.id}`}
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// -------- Pipeline (Kanban 5 fasi) + Storico cliente --------
const ageHours = (iso) => {
  if (!iso) return 999999;
  const d = new Date(iso).getTime();
  if (Number.isNaN(d)) return 999999;
  return Math.max(0, (Date.now() - d) / (3600 * 1000));
};

function PipelineTab({ contracts, bookings, reload }) {
  const { t } = useTranslation();
  const [historyEmail, setHistoryEmail] = React.useState(null);
  const [marking, setMarking] = React.useState({});
  const [manageContract, setManageContract] = React.useState(null);

  const buckets = React.useMemo(() => {
    const bk = { new_requests: [], to_contact: [], scheduled: [], done_test: [], completed: [] };
    for (const c of contracts) {
      if (c.status === "cancelled") continue;
      if (c.status === "completed") {
        bk.completed.push(c);
      } else if (c.status === "test_done") {
        bk.done_test.push(c);
      } else if (c.first_contact_at) {
        // Contacted → In agenda (has a preferred date fixed by the client)
        bk.scheduled.push(c);
      } else if (ageHours(c.created_at) < 24) {
        bk.new_requests.push(c);
      } else {
        bk.to_contact.push(c);
      }
    }
    return bk;
  }, [contracts]);

  const markContacted = async (c) => {
    setMarking((m) => ({ ...m, [c.id]: true }));
    try {
      await api.patch(`/admin/contracts/${c.id}`, {
        first_contact_at: new Date().toISOString(),
      });
      toast.success(t("admin.status_updated"));
      reload();
    } catch {
      toast.error(t("admin.error"));
    } finally {
      setMarking((m) => ({ ...m, [c.id]: false }));
    }
  };

  const cols = [
    { key: "new_requests", icon: <Mail className="h-4 w-4" />, color: "text-sky-600", ring: "ring-sky-200", bg: "bg-sky-50" },
    { key: "to_contact",   icon: <AlertTriangle className="h-4 w-4" />, color: "text-red-600", ring: "ring-red-200", bg: "bg-red-50" },
    { key: "scheduled",    icon: <CalendarClock className="h-4 w-4" />, color: "text-amber-600", ring: "ring-amber-200", bg: "bg-amber-50" },
    { key: "done_test",    icon: <Check className="h-4 w-4" />, color: "text-emerald-600", ring: "ring-emerald-200", bg: "bg-emerald-50" },
    { key: "completed",    icon: <Check className="h-4 w-4" />, color: "text-slate-600", ring: "ring-slate-200", bg: "bg-slate-50" },
  ];

  return (
    <div className="mt-6" data-testid="pipeline-tab">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-lg font-semibold text-navy flex items-center gap-2">
            <Workflow className="h-5 w-5 text-[#5BA4D4]" />
            {t("admin.pipeline.tab")}
          </h3>
          <p className="text-sm text-slate-500 mt-0.5">{t("admin.pipeline.subtitle")}</p>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4" data-testid="pipeline-columns">
        {cols.map(({ key, icon, color, ring, bg }) => {
          const items = buckets[key];
          return (
            <div key={key} className={`rounded-xl border border-slate-200 ${bg}`} data-testid={`pipeline-col-${key}`}>
              <div className={`flex items-center gap-2 px-3 pt-3 pb-2 border-b border-slate-200 ${color}`}>
                {icon}
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold uppercase tracking-wider truncate">
                    {t(`admin.pipeline.${key}`)}
                  </p>
                  <p className="text-[10px] text-slate-500 truncate">
                    {t(`admin.pipeline.${key}_hint`)}
                  </p>
                </div>
                <span className={`ml-auto text-xs font-bold rounded-full ring-1 ${ring} bg-white px-2 py-0.5`}>
                  {items.length}
                </span>
              </div>
              <div className="p-2 space-y-2 min-h-[80px]">
                {items.length === 0 ? (
                  <p className="text-xs text-slate-400 italic text-center py-4">{t("admin.pipeline.empty_col")}</p>
                ) : (
                  items.map((c) => (
                    <PipelineCard
                      key={c.id}
                      c={c}
                      col={key}
                      onContact={() => markContacted(c)}
                      onOpenHistory={() => setHistoryEmail(c.client_email)}
                      onManage={() => setManageContract(c)}
                      marking={!!marking[c.id]}
                    />
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {historyEmail ? (
        <ClientHistoryModal
          email={historyEmail}
          onClose={() => setHistoryEmail(null)}
          allBookings={bookings.filter((b) => b.email?.toLowerCase() === historyEmail.toLowerCase())}
        />
      ) : null}

      {manageContract ? (
        <ContractManagerModal
          contract={manageContract}
          onClose={() => setManageContract(null)}
          onChanged={reload}
        />
      ) : null}
    </div>
  );
}

function PipelineCard({ c, col, onContact, onOpenHistory, onManage, marking }) {
  const { t } = useTranslation();
  const isUrgent = col === "to_contact";
  return (
    <div
      className={`bg-white rounded-lg border border-slate-200 p-3 shadow-sm hover:shadow-md transition ${
        isUrgent ? "border-l-4 border-l-red-500" : ""
      }`}
      data-testid={`pipeline-card-${c.id}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="font-medium text-navy text-sm truncate">{c.client_name}</p>
          <p className="text-xs text-slate-500 truncate">
            {c.date} · {c.time_slot}
          </p>
          <p className="text-xs text-[#5BA4D4] font-semibold mt-0.5">
            {c.service_label} · €{c.service_price}
          </p>
        </div>
        {isUrgent ? (
          <span className="rounded-full bg-red-100 text-red-700 text-[10px] px-1.5 py-0.5 font-semibold flex-shrink-0">
            {t("admin.pipeline.urgent")}
          </span>
        ) : null}
      </div>

      <div className="mt-2 flex gap-1 text-xs">
        <a
          href={`tel:${c.client_phone}`}
          className="rounded-md bg-slate-100 hover:bg-slate-200 p-1.5"
          title={c.client_phone}
          data-testid={`pipeline-call-${c.id}`}
        >
          <Phone className="h-3 w-3" />
        </a>
        <a
          href={`https://wa.me/${(c.client_phone || "").replace(/[^\d]/g, "")}`}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-md bg-emerald-100 hover:bg-emerald-200 p-1.5 text-emerald-700"
          title="WhatsApp"
          data-testid={`pipeline-wa-${c.id}`}
        >
          <MessageSquareIcon />
        </a>
        <a
          href={`mailto:${c.client_email}`}
          className="rounded-md bg-slate-100 hover:bg-slate-200 p-1.5"
          title={c.client_email}
          data-testid={`pipeline-email-${c.id}`}
        >
          <Mail className="h-3 w-3" />
        </a>
        <button
          onClick={onOpenHistory}
          className="rounded-md bg-slate-100 hover:bg-slate-200 p-1.5"
          title={t("admin.pipeline.history_title")}
          data-testid={`pipeline-history-${c.id}`}
        >
          <History className="h-3 w-3" />
        </button>
        <button
          onClick={onManage}
          className="rounded-md bg-navy hover:bg-navy/90 text-white p-1.5 ml-auto"
          title={t("admin.tools.manage")}
          data-testid={`pipeline-manage-${c.id}`}
        >
          <Zap className="h-3 w-3" />
        </button>
      </div>

      {(col === "new_requests" || col === "to_contact") && (
        <button
          onClick={onContact}
          disabled={marking}
          className="mt-2 w-full text-xs rounded-md bg-navy hover:bg-navy/90 text-white px-2 py-1.5 font-medium flex items-center justify-center gap-1 disabled:opacity-40"
          data-testid={`pipeline-mark-contacted-${c.id}`}
        >
          <UserCheck className="h-3 w-3" />
          {t("admin.pipeline.mark_contacted")}
        </button>
      )}
      {c.first_contact_at && col !== "new_requests" && col !== "to_contact" ? (
        <p className="mt-2 text-[10px] text-slate-500">
          {t("admin.pipeline.contacted_at")}: {new Date(c.first_contact_at).toLocaleString()}
        </p>
      ) : null}
    </div>
  );
}

function MessageSquareIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
    </svg>
  );
}

function ClientHistoryModal({ email, onClose, allBookings }) {
  const { t } = useTranslation();
  const [detail, setDetail] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    api
      .get(`/admin/clients/${encodeURIComponent(email)}/detail`)
      .then((r) => setDetail(r.data))
      .catch(() => setDetail({ error: true }))
      .finally(() => setLoading(false));
  }, [email]);

  const timeline = React.useMemo(() => {
    if (!detail || detail.error) return [];
    const evts = [];
    for (const b of detail.bookings || []) {
      evts.push({ ts: b.created_at, kind: "booking_created", label: `Réservation créée — ${b.date} ${b.time_slot}`, data: b });
    }
    for (const c of detail.contracts || []) {
      evts.push({ ts: c.created_at, kind: "contract", label: `Contrat signé — ${c.service_label} €${c.service_price}`, data: c });
      if (c.first_contact_at) {
        evts.push({ ts: c.first_contact_at, kind: "contacted", label: "Premier contact effectué", data: c });
      }
      if (c.photo_after_uploaded_at) {
        evts.push({ ts: c.photo_after_uploaded_at, kind: "test_done", label: "Test effectué (photo après)", data: c });
      }
    }
    return evts
      .filter((e) => e.ts)
      .sort((a, b) => new Date(b.ts) - new Date(a.ts));
  }, [detail]);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
      data-testid="client-history-modal"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col"
      >
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-wider text-slate-500">{t("admin.pipeline.history_title")}</p>
            <p className="font-semibold text-navy truncate">{email}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-100"
            data-testid="close-history"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto flex-1">
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin text-slate-400 mx-auto" />
          ) : detail?.error ? (
            <p className="text-sm text-red-600">{t("admin.error")}</p>
          ) : (
            <>
              {detail?.stats ? (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-5">
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-[10px] uppercase text-slate-500">Réservations</p>
                    <p className="text-lg font-semibold text-navy">{detail.stats.total_bookings}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-[10px] uppercase text-slate-500">Contrats</p>
                    <p className="text-lg font-semibold text-navy">{detail.stats.total_contracts}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-[10px] uppercase text-slate-500">CA</p>
                    <p className="text-lg font-semibold text-[#5BA4D4]">€{Math.round(detail.stats.total_spent)}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-[10px] uppercase text-slate-500">Dernière visite</p>
                    <p className="text-sm font-semibold text-navy">{detail.stats.last_visit || "—"}</p>
                  </div>
                </div>
              ) : null}

              <ol className="relative border-l-2 border-slate-200 ml-2 space-y-4">
                {timeline.length === 0 ? (
                  <p className="text-sm text-slate-500 py-4">—</p>
                ) : (
                  timeline.map((e, i) => (
                    <li key={`${e.kind}-${i}`} className="ml-4">
                      <span className="absolute -left-[7px] w-3 h-3 rounded-full bg-[#5BA4D4] border-2 border-white" />
                      <p className="text-xs text-slate-500">
                        {new Date(e.ts).toLocaleString()}
                      </p>
                      <p className="text-sm text-navy font-medium mt-0.5">{e.label}</p>
                    </li>
                  ))
                )}
              </ol>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
