// Página de autenticación con dos modos: login y registro.
//
// Layout ambicioso para contexto universitario:
//   - Panel izquierdo (solo desktop): branding con gradiente índigo,
//     formas decorativas geométricas, features con badges ámbar.
//   - Panel derecho: formulario con iconos en inputs, sombras pronunciadas
//     y micro-animaciones de entrada.
//
// En modo login pide email + contraseña.
// En modo registro pide nombre, apellido, email, contraseña y confirmación.
// Los errores del backend se muestran como toasts (sonner).
// Al enviar exitosamente, redirige al dashboard (/).

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/contexto-auth/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ModeToggle } from "@/components/mode-toggle";
import {
  Eye,
  EyeOff,
  BrainCircuit,
  BarChart3,
  Trophy,
  Mail,
  Lock,
  User,
  GraduationCap,
  ArrowRight,
} from "lucide-react";
import { toast } from "sonner";
import { CanvasParticulas } from "@/components/efectos/canvas-particulas";

// Lista de features destacados en el panel de branding.
const features = [
  {
    icon: BrainCircuit,
    titulo: "IA Multi-Agente",
    descripcion: "Sistema inteligente que se adapta a tu ritmo de aprendizaje",
  },
  {
    icon: BarChart3,
    titulo: "Progreso Medible",
    descripcion: "Análisis detallado de tu evolución académica",
  },
  {
    icon: Trophy,
    titulo: "Gamificación",
    descripcion: "Logros, niveles y recompensas por tu esfuerzo",
  },
];

type Modo = "login" | "registro";

export default function PaginaLogin() {
  const { iniciarSesion, registrar } = useAuth();
  const navigate = useNavigate();

  // Estado del formulario
  const [modo, setModo] = useState<Modo>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [secondName, setSecondName] = useState("");
  const [firstLastName, setFirstLastName] = useState("");
  const [secondLastName, setSecondLastName] = useState("");
  const [cargando, setCargando] = useState(false);
  const [mostrarPassword, setMostrarPassword] = useState(false);
  const [mostrarConfirmPassword, setMostrarConfirmPassword] = useState(false);

  // Resetea todos los campos del formulario.
  const limpiarFormulario = () => {
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setFirstName("");
    setSecondName("");
    setFirstLastName("");
    setSecondLastName("");
    setMostrarPassword(false);
    setMostrarConfirmPassword(false);
  };

  // Alterna entre login y registro, limpiando el formulario.
  const alternarModo = () => {
    setModo(modo === "login" ? "registro" : "login");
    limpiarFormulario();
  };

  // Envía credenciales de login al contexto de auth.
  const manejarLogin = async () => {
    await iniciarSesion({ email, password });
  };

  // Envía datos de registro al contexto de auth.
  // Valida que las contraseñas coincidan antes de enviar.
  const manejarRegistro = async () => {
    if (password !== confirmPassword) {
      throw new Error("passwords_mismatch");
    }
    await registrar({
      first_name: firstName,
      second_name: secondName || undefined,
      first_last_name: firstLastName,
      second_last_name: secondLastName || undefined,
      email,
      password,
    });
  };

  // Handler principal del formulario: ejecuta login o registro según el modo.
  // Maneja errores del backend y los muestra como toasts.
  const manejarSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCargando(true);

    try {
      if (modo === "login") {
        await manejarLogin();
      } else {
        await manejarRegistro();
      }
      navigate("/");
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { data?: Record<string, string[]> };
      };
      const data = axiosErr.response?.data;

      if (modo === "login") {
        if (data) {
          const mensajes = Object.values(data).flat().join(". ");
          toast.error(mensajes);
        } else {
          toast.error("Credenciales incorrectas");
        }
      } else {
        if (err instanceof Error && err.message === "passwords_mismatch") {
          toast.error("Las contraseñas no coinciden");
        } else if (data) {
          const mensajes = Object.values(data).flat().join(". ");
          toast.error(mensajes);
        } else {
          toast.error("Error al crear la cuenta");
        }
      }
    } finally {
      setCargando(false);
    }
  };

  const esLogin = modo === "login";

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      {/* Toggle tema - posición fija en esquina superior derecha */}
      <div className="fixed top-4 right-4 z-10">
        <ModeToggle />
      </div>

      {/* Contenedor principal: dos paneles lado a lado en desktop */}
      <div className="flex w-full max-w-7xl h-180 rounded-2xl overflow-hidden border bg-card shadow-2xl shadow-primary/8">
        {/* ═══════════════════════════════════════════════════════════
            PANEL IZQUIERDO - Branding universitario (oculto en móvil)
            ═══════════════════════════════════════════════════════════ */}
        <div className="relative hidden lg:flex lg:w-[55%] flex-col justify-between overflow-hidden">
          {/* Fondo con gradiente índigo profundo */}
          <div className="absolute inset-0 bg-gradient-to-br from-[#1a1145] via-[#1e1550] to-[#0f0a2e]" />

          {/* Formas decorativas geométricas */}
          {/* Anillo grande semitransparente - esquina superior derecha */}
          <div className="absolute -top-20 -right-20 h-80 w-80 rounded-full border-[3px] border-white/[0.06] animate-pulse" style={{ animationDuration: "8s" }} />
          <div className="absolute -top-10 -right-10 h-60 w-60 rounded-full border-[2px] border-white/[0.04]" />

          {/* Círculo con blur - esquina inferior izquierda */}
          <div className="absolute -bottom-16 -left-16 h-64 w-64 rounded-full bg-accent/10 blur-3xl" />

          {/* Línea diagonal sutil */}
          <div
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage:
                "linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.1) 50%, transparent 60%)",
            }}
          />

          {/* Partículas con efecto de constelación / red neuronal */}
          <CanvasParticulas />

          {/* Contenido del branding */}
          <div className="relative z-10 flex flex-col h-full p-10">
            {/* Logo con badge ámbar */}
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 backdrop-blur-sm border border-white/10">
                <BrainCircuit className="h-5 w-5 text-white" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-white tracking-tight">
                  PseudoTutor
                </span>
                <span className="rounded-full bg-accent/90 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-accent-foreground">
                  IA
                </span>
              </div>
            </div>

            {/* Título y descripción */}
            <div className="mt-auto space-y-4">
              <div className="flex items-center gap-2 text-accent/80">
                <GraduationCap className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-widest">
                  Corporación Universitaria Autónoma del Cauca
                </span>
              </div>

              <h2 className="text-3xl xl:text-4xl font-bold leading-[1.15] text-white tracking-tight">
                Transforma tu
                <br />
                experiencia
                <br />
                <span className="bg-gradient-to-r from-accent to-amber-300 bg-clip-text text-transparent">
                  universitaria
                </span>
              </h2>

              <p className="text-sm text-white/50 max-w-sm leading-relaxed">
                Plataforma de aprendizaje adaptativo potenciada por inteligencia
                artificial, diseñada para tu éxito académico.
              </p>
            </div>

            {/* Tarjetas de features */}
            <div className="mt-8 grid gap-2.5">
              {features.map((feature, index) => (
                <div
                  key={feature.titulo}
                  className="group flex items-start gap-3.5 rounded-xl bg-white/[0.04] p-3.5 backdrop-blur-sm border border-white/[0.06] transition-all duration-300 hover:bg-white/[0.08] hover:border-white/[0.12] hover:translate-x-1"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent/15 border border-accent/20">
                    <feature.icon className="h-4 w-4 text-accent" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white/90">
                      {feature.titulo}
                    </h3>
                    <p className="text-xs text-white/40 leading-relaxed mt-0.5">
                      {feature.descripcion}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Stats en la parte inferior */}
            <div className="mt-8 flex items-center gap-5 text-xs text-white/30">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
                </span>
                Sistema activo
              </div>
              <div className="h-3 w-px bg-white/10" />
              <div>+2,500 estudiantes</div>
              <div className="h-3 w-px bg-white/10" />
              <div>4.8★ valoración</div>
            </div>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════
            PANEL DERECHO - Formulario de login/registro
            ═══════════════════════════════════════════════════════════ */}
        <div className="relative flex w-full items-center justify-center p-6 sm:p-8 lg:w-[45%]">
          {/* Fondo sutil con gradiente en móvil */}
          <div className="absolute inset-0 bg-gradient-to-b from-primary/[0.02] to-transparent lg:from-transparent" />

          <div className="relative w-full max-w-sm space-y-6">
            {/* Logo visible solo en móvil */}
            <div className="text-center space-y-3 lg:hidden">
              <div className="inline-flex items-center justify-center gap-2.5">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 shadow-lg shadow-primary/10">
                  <BrainCircuit className="h-6 w-6 text-primary" />
                </div>
                <h1 className="text-2xl font-bold tracking-tight">
                  <span className="text-foreground">Pseudo</span>
                  <span className="text-primary">Tutor</span>
                </h1>
              </div>
              <p className="text-xs text-muted-foreground">
                Aprendizaje adaptativo con inteligencia artificial
              </p>
            </div>

            {/* Título dinámico según modo */}
            <div className="space-y-1.5">
              <h2 className="text-2xl font-bold text-foreground tracking-tight">
                {esLogin ? "Bienvenido de vuelta" : "Crea tu cuenta"}
              </h2>
              <p className="text-sm text-muted-foreground">
                {esLogin
                  ? "Inicia sesión para continuar con tu aprendizaje"
                  : "Regístrate para empezar a aprender con IA"}
              </p>
            </div>

            {/* Formulario: key={modo} fuerza re-mount al cambiar de modo */}
            <form
              key={modo}
              onSubmit={manejarSubmit}
              className="space-y-4 animate-in fade-in slide-in-from-bottom-3 duration-300"
            >
              {/* Campos de nombre y apellido (solo en modo registro) */}
              {!esLogin && (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label
                        htmlFor="firstName"
                        className="text-sm font-medium"
                      >
                        Nombre *
                      </Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/60" />
                        <Input
                          id="firstName"
                          type="text"
                          value={firstName}
                          onChange={(e) => setFirstName(e.target.value)}
                          placeholder="Juan"
                          className="h-10 pl-9"
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <Label
                        htmlFor="firstLastName"
                        className="text-sm font-medium"
                      >
                        Apellido *
                      </Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/60" />
                        <Input
                          id="firstLastName"
                          type="text"
                          value={firstLastName}
                          onChange={(e) => setFirstLastName(e.target.value)}
                          placeholder="Pérez"
                          className="h-10 pl-9"
                          required
                        />
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label
                        htmlFor="secondName"
                        className="text-sm font-medium"
                      >
                        2do nombre
                      </Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/60" />
                        <Input
                          id="secondName"
                          type="text"
                          value={secondName}
                          onChange={(e) => setSecondName(e.target.value)}
                          placeholder="Carlos"
                          className="h-10 pl-9"
                        />
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <Label
                        htmlFor="secondLastName"
                        className="text-sm font-medium"
                      >
                        2do apellido
                      </Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/60" />
                        <Input
                          id="secondLastName"
                          type="text"
                          value={secondLastName}
                          onChange={(e) => setSecondLastName(e.target.value)}
                          placeholder="López"
                          className="h-10 pl-9"
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Campo de email */}
              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-sm font-medium">
                  Correo electrónico
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/60" />
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="tu@email.com"
                    className="h-10 pl-9"
                    required
                  />
                </div>
              </div>

              {/* Campo de contraseña con toggle de visibilidad */}
              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-sm font-medium">
                  Contraseña
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/60" />
                  <Input
                    id="password"
                    type={mostrarPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="h-10 pl-9 pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setMostrarPassword(!mostrarPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/60 hover:text-foreground transition-colors"
                  >
                    {mostrarPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Confirmar contraseña (solo en modo registro) */}
              {!esLogin && (
                <div className="space-y-1.5">
                  <Label
                    htmlFor="confirmPassword"
                    className="text-sm font-medium"
                  >
                    Confirmar contraseña
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/60" />
                    <Input
                      id="confirmPassword"
                      type={mostrarConfirmPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      className="h-10 pl-9 pr-10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setMostrarConfirmPassword(!mostrarConfirmPassword)
                      }
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/60 hover:text-foreground transition-colors"
                    >
                      {mostrarConfirmPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Botón de envío */}
              <Button
                type="submit"
                className="w-full h-11 text-sm font-semibold shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-shadow duration-300 group/btn"
                disabled={cargando}
              >
                {cargando ? (
                  <div className="flex items-center gap-2">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                    {esLogin ? "Iniciando sesión..." : "Creando cuenta..."}
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    {esLogin ? "Iniciar sesión" : "Crear cuenta"}
                    <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover/btn:translate-x-0.5" />
                  </div>
                )}
              </Button>
            </form>

            {/* Separador visual */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-card px-3 text-muted-foreground">
                  {esLogin ? "¿Primera vez aquí?" : "¿Ya tienes cuenta?"}
                </span>
              </div>
            </div>

            {/* Link para alternar entre login y registro */}
            <div className="text-center">
              <button
                type="button"
                onClick={alternarModo}
                className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:text-primary/80 transition-colors group/link"
              >
                {esLogin ? "Crear una cuenta" : "Iniciar sesión"}
                <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover/link:translate-x-0.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
