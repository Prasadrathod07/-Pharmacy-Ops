import { useState } from "react";

import { Input, StatusBadge } from "../../../components/ui";
import { useDrugs } from "../../drugs/hooks";
import { useDebouncedValue } from "../../../hooks/useDebouncedValue";
import type { DrugListItem } from "../../../types";
import styles from "./DrugPicker.module.css";

interface DrugPickerProps {
  onSelect: (drug: DrugListItem) => void;
  excludeDrugIds?: number[];
}

export function DrugPicker({ onSelect, excludeDrugIds = [] }: DrugPickerProps) {
  const [searchText, setSearchText] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const debouncedSearch = useDebouncedValue(searchText, 250);

  const { data, isLoading, isError } = useDrugs({
    search: debouncedSearch || undefined,
    active: true,
    page_size: 10,
  });
  const results = (data?.items ?? []).filter((drug) => !excludeDrugIds.includes(drug.id));

  return (
    <div className={styles.wrapper}>
      <Input
        placeholder="Search medicine by name or code..."
        value={searchText}
        onChange={(event) => {
          setSearchText(event.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setIsOpen(false)}
      />
      {isOpen && searchText.trim() ? (
        <div className={styles.resultsPanel}>
          {isLoading ? (
            <div className={styles.resultRow}>Searching...</div>
          ) : isError ? (
            <div className={styles.resultRow}>Could not search medicines. Please try again.</div>
          ) : results.length === 0 ? (
            <div className={styles.resultRow}>No matching medicines.</div>
          ) : (
            results.map((drug) => (
              <button
                key={drug.id}
                type="button"
                className={styles.resultRow}
                // onMouseDown fires before the input's onBlur closes the panel,
                // so the click still registers.
                onMouseDown={(event) => {
                  event.preventDefault();
                  onSelect(drug);
                  setSearchText("");
                  setIsOpen(false);
                }}
              >
                <div>
                  <div className={styles.resultName}>
                    {drug.name} {drug.strength ?? ""}
                  </div>
                  <div className={styles.resultMeta}>
                    {drug.code} · {drug.dosage_form ?? "—"}
                  </div>
                </div>
                <div className={styles.resultRight}>
                  <StatusBadge status={drug.stock_status} />
                  <span className={styles.resultMeta}>{drug.quantity_on_hand} in stock</span>
                </div>
              </button>
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}
