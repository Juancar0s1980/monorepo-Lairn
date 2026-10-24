// Página pública para solicitar el correo de recuperación de contraseña.
// Siempre muestra el mismo mensaje de éxito, exista o no ese correo
// (el backend responde igual en ambos casos para no revelar cuentas).

import { useState } from "react";
import { Link } from "react-router-dom";
import api from "@/services/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ModeToggle } from "@/components/mode-toggle";
import { Mail, ArrowLeft, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { MascotaRobot } from "@/components/mascota-robot";

export default function PaginaRecuperarContrasena() {
  const [email, setEmail] = useState("");
  const [cargando, setCargando] = useState(false);
  const [enviado, setEnviado] = useState(false);

  const manejarSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCargando(true);
    try {
      await api.post("/usuarios/recuperar-contrasena/", { email });
      setEnviado(true);
    } catch {
      toast.error("Correo inválido, intenta de nuevo");
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
            ¿Olvidaste tu contraseña?
          </h2>
          <p className="text-sm text-muted-foreground">
            Ingresa tu correo y te enviaremos un enlace para restablecerla.
          </p>
        </div>

        {enviado ? (
          <div className="flex flex-col items-center gap-3 rounded-xl border border-success/30 bg-success/10 p-5 text-center">
            <CheckCircle2 className="h-8 w-8 text-success" />
            <p className="text-sm text-foreground">
              Si <strong>{email}</strong> está registrado, te enviamos un
              enlace para restablecer tu contraseña. Revisa tu bandeja de
              entrada.
            </p>
          </div>
        ) : (
          <form onSubmit={manejarSubmit} className="space-y-4">
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

            <Button
              type="submit"
              className="w-full h-11 text-sm font-semibold"
              disabled={cargando}
            >
              {cargando ? "Enviando..." : "Enviar enlace de recuperación"}
            </Button>
          </form>
        )}

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
