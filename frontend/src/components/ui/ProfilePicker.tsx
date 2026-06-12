import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";

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
};

export function ProfilePicker<TProfile extends { profile: Profile }>({
  label,
  queryKey,
  activeQueryKey,
  listProfiles,
  getActiveProfile,
  createProfile,
  setActiveProfile
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

  const handleCreate = () => {
    const name = window.prompt(`Название профиля ${label}`);
    if (name?.trim()) create.mutate(name.trim());
  };

  return (
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
      <Button icon={<Plus size={16} />} onClick={handleCreate}>
        Новый
      </Button>
    </div>
  );
}
