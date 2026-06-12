import { useQuery } from "@tanstack/react-query";
import { Blocks, Server, Waypoints } from "lucide-react";

import { api } from "../lib/api";
import { Card } from "../components/ui/Card";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { StatusBadge } from "../components/ui/StatusBadge";

export function ServersScreen() {
  const profile = useQuery({ queryKey: ["active-profile"], queryFn: api.activeProfile });

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="Server collections"
        title="Сборки и окружения"
        description="Здесь видно, какие Minecraft, VPS и frpc профили сейчас складываются в один запуск."
      />

      <div className="card-grid">
        <Card title="Minecraft-сборка" eyebrow="Server" className="feature-card">
          <Blocks size={32} />
          <h3>{profile.data?.minecraft.server_type || "Vanilla"}</h3>
          <p>{profile.data?.minecraft.server_dir || "Папка сервера не выбрана"}</p>
          <StatusBadge status={profile.data?.minecraft.jar_path ? "OK" : "WARNING"} />
        </Card>
        <Card title="VPS-сервер" eyebrow="Network" className="feature-card">
          <Server size={32} />
          <h3>{profile.data?.vps.host || "VPS не задан"}</h3>
          <p>{profile.data?.vps.username || "SSH пользователь не задан"}</p>
          <StatusBadge status={profile.data?.vps.host ? "OK" : "WARNING"} />
        </Card>
        <Card title="Публичный туннель" eyebrow="FRP" className="feature-card">
          <Waypoints size={32} />
          <h3>{profile.data?.tunnel.remote_port || 25565}</h3>
          <p>{profile.data?.tunnel.frp_server_addr || profile.data?.vps.host || "FRP host не задан"}</p>
          <StatusBadge status={profile.data?.tunnel.frp_token ? "OK" : "WARNING"} />
        </Card>
      </div>
    </div>
  );
}
