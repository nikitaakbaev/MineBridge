import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";

import type { Profile } from "../../lib/types";
import { Button } from "./Button";
import { SelectInput } from "./Field";

type ProfilePickerProps<TProfile> = {
  label: string;
  queryKey: string[];
  activeQueryKey: string[];
  listProfiles: () => Promise<Profile[]>;
  getActiveProfile: () => Promise<TProfile>;
  createProfile: (name: string) => Promise<TProfile>;
  setActiveProfile: (id: number) => Promise<TProfile>;
  renameProfile: (id: number, name: string) => Promise<TProfile>;
  deleteProfile: (id: number) => Promise<TProfile>;
};

export function ProfilePicker<TProfile extends { profile: Profile }>({
  label,
  queryKey,
  activeQueryKey,
  listProfiles,
  getActiveProfile,
  createProfile,
  setActiveProfile,
  renameProfile,
  deleteProfile
}: ProfilePickerProps<TProfile>) {
  const queryClient = useQueryClient();
  const profiles = useQuery({ queryKey, queryFn: listProfiles });
  const active = useQuery({ queryKey: activeQueryKey, queryFn: getActiveProfile });
  const setActive = useMutation({
    mutationFn: setActiveProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({ queryKey: activeQueryKey });
      queryClient.invalidateQueries({ queryKey: ["active-profile"] });
    }
  });
  const create = useMutation({
    mutationFn: createProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({ queryKey: activeQueryKey });
    }
  });
  const rename = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) => renameProfile(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({ queryKey: activeQueryKey });
      queryClient.invalidateQueries({ queryKey: ["active-profile"] });
    }
  });
  const remove = useMutation({
    mutationFn: deleteProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({ queryKey: activeQueryKey });
      queryClient.invalidateQueries({ queryKey: ["active-profile"] });
    }
  });

  const handleCreate = () => {
    const name = window.prompt(`Название профиля ${label}`);
    if (name?.trim()) create.mutate(name.trim());
  };

  const handleRename = () => {
    const profile = active.data?.profile;
    if (!profile?.id) return;
    const name = window.prompt(`Новое название профиля ${label}`, profile.name);
    if (name?.trim()) rename.mutate({ id: profile.id, name: name.trim() });
  };

  const handleDelete = () => {
    const profile = active.data?.profile;
    if (!profile?.id) return;
    if (window.confirm(`Удалить профиль «${profile.name}»?`)) {
      remove.mutate(profile.id);
    }
  };

  const error =
    profiles.error || active.error || setActive.error || create.error || rename.error || remove.error;

  return (
    <div className="profile-picker-wrap">
      <div className="profile-picker">
        <div>
          <span>{label}</span>
          <strong>{active.data?.profile.name || "Профиль не выбран"}</strong>
        </div>
        <SelectInput
          value={active.data?.profile.id ?? ""}
          onChange={(event) => setActive.mutate(Number(event.target.value))}
        >
          {(profiles.data || []).map((profile) => (
            <option key={profile.id ?? profile.name} value={profile.id ?? ""}>
              {profile.name}
            </option>
          ))}
        </SelectInput>
        <details className="profile-menu">
          <summary aria-label={`Действия профиля ${label}`}>
            <MoreHorizontal size={18} />
          </summary>
          <div className="profile-menu-panel">
            <Button icon={<Plus size={16} />} onClick={handleCreate}>
              Новый профиль
            </Button>
            <Button icon={<Pencil size={16} />} onClick={handleRename} disabled={!active.data?.profile.id}>
              Переименовать
            </Button>
            <Button
              variant="danger"
              icon={<Trash2 size={16} />}
              onClick={handleDelete}
              disabled={!active.data?.profile.id}
            >
              Удалить
            </Button>
          </div>
        </details>
      </div>
      {error && <div className="inline-error">{(error as Error).message}</div>}
    </div>
  );
}
