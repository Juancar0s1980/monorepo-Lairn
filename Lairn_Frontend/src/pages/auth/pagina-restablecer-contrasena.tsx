// Página pública para elegir una nueva contraseña, llegando desde el enlace
// del correo de recuperación (/restablecer-contrasena/:uid/:token/).

import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import api from "@/services/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ModeToggle } from "@/components/mode-toggle";
import { Lock, Eye, EyeOff, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { MascotaRobot } from "@/components/mascota-robot";

export default function PaginaRestablecerContrasena() {
  const { uid, token } = useParams<{ uid: string; token: string }>();
  const navigate = useNavigate();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [mostrarPassword, setMostrarPassword] = useState(false);
  const [cargando, setCargando] = useState(false);

  const manejarSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast.error("Las contraseñas no coinciden");
      return;
    }

    setCargando(true);
    try {
      await api.post("/usuarios/restablecer-contrasena/", {
        uid,
        token,
        password,
      });
      toast.success("Tu contraseña fue actualizada correctamente");
      navigate("/iniciar-sesion");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, string[]> } };
      const data = axiosErr.response?.data;
      if (data) {
        toast.error(Object.values(data).flat().join(". "));
      } else {
        toast.error("El enlace no es válido o ya venció");
      }
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="flex min-h-screen w-screen items-center justify-center bg-background p-4">
      <div className="fixed top-4 right-4 z-10">
        <ModeToggle />
      </div>

      <div className="w-full max-w-sm space-y-6 rounded-2xl border bg-card p-8 shadow-2xl shadow-primary/8">
        <div className="text-center space-y-3">
          <div className="relative mx-auto flex h-20 items-center justify-center">
            <MascotaRobot className="relative h-full w-auto" />
          </div>
          <h2 className="font-heading text-xl text-foreground tracking-tight">
            Elige tu nueva contraseña
          </h2>
          <p className="text-sm text-muted-foreground">
            Debe tener al menos 8 caracteres y no ser demasiado común.
          </p>
        </div>

        <form onSubmit={manejarSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="password" className="text-sm font-medium">
              Nueva contraseña
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

          <div className="space-y-1.5">
            <Label htmlFor="confirmPassword" className="text-sm font-medium">
              Confirmar contraseña
            </Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/60" />
              <Input
                id="confirmPassword"
                type={mostrarPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className="h-10 pl-9"
                required
              />
            </div>
          </div>

          <Button
            type="submit"
            className="w-full h-11 text-sm font-semibold"
            disabled={cargando}
          >
            {cargando ? "Actualizando..." : "Restablecer contraseña"}
          </Button>
        </form>

        <div className="text-center">
          <Link
            to="/iniciar-sesion"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:text-primary-hover dark:hover:text-primary/80 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Volver a iniciar sesión
          </Link>
        </div>
      </div>
    </div>
  );
}
