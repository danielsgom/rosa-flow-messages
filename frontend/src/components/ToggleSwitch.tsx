import React from 'react';

interface ToggleSwitchProps {
  enabled: boolean;
  onChange: () => void;
  size?: 'sm' | 'md';
}

export const ToggleSwitch: React.FC<ToggleSwitchProps> = ({ enabled, onChange, size = 'md' }) => {
  const track = size === 'sm'
    ? 'w-7 h-4 peer-checked:after:translate-x-3 after:h-3 after:w-3 peer-focus:ring-2'
    : 'w-11 h-6 peer-checked:after:translate-x-5 after:h-5 after:w-5 peer-focus:ring-4';

  return (
    <label className="relative inline-flex items-center cursor-pointer">
      <input
        type="checkbox"
        className="sr-only peer"
        checked={enabled}
        onChange={onChange}
      />
      <div className={`${track} bg-gray-200 peer-focus:outline-none peer-focus:ring-rosa-300 rounded-full peer peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:border-gray-300 after:border after:rounded-full after:transition-all peer-checked:bg-rosa-600`}></div>
    </label>
  );
};
