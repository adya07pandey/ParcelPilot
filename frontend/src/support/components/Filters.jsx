import { Search } from "lucide-react";
import { formatOptionLabel } from "../utils";

export function SearchBox({ value, onChange, placeholder }) {
  return (
    <label className="support-search">
      <Search size={18} />
      <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
    </label>
  );
}

export function SelectFilter({ label, value, onChange, options }) {
  return (
    <label className="support-filter">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => {
          const optionValue = typeof option === "object" ? option.value : option;
          const optionLabel = typeof option === "object" ? option.label : formatOptionLabel(option);
          return (
            <option key={optionValue} value={optionValue}>
              {optionLabel}
            </option>
          );
        })}
      </select>
    </label>
  );
}
