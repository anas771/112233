(function () {
  var container = document.getElementById("treatment-rows");
  var addBtn = document.getElementById("add-treatment-row");
  if (!container || !addBtn) {
    return;
  }

  var firstRow = container.querySelector(".treatment-row");
  if (!firstRow) {
    return;
  }

  function wireRow(row) {
    var select = row.querySelector("select[name='treatment_catalog_id[]']");
    var removeBtn = row.querySelector(".remove-treatment-row");

    if (select) {
      select.addEventListener("change", function () {
        var option = select.options[select.selectedIndex];
        if (!option) {
          return;
        }
        var nameInput = row.querySelector("input[name='treatment_name[]']");
        var activeInput = row.querySelector("input[name='treatment_active[]']");
        var classInput = row.querySelector("input[name='treatment_class[]']");

        if (nameInput && option.dataset.name && !nameInput.value.trim()) {
          nameInput.value = option.dataset.name;
        }
        if (activeInput && option.dataset.active && !activeInput.value.trim()) {
          activeInput.value = option.dataset.active;
        }
        if (classInput && option.dataset.class && !classInput.value.trim()) {
          classInput.value = option.dataset.class;
        }
      });
    }

    if (!removeBtn) {
      return;
    }

    removeBtn.addEventListener("click", function () {
      if (container.children.length === 1) {
        row.querySelectorAll("input").forEach(function (input) {
          input.value = "";
        });
        if (select) {
          select.value = "";
        }
        return;
      }
      row.remove();
    });
  }

  wireRow(firstRow);

  addBtn.addEventListener("click", function () {
    var clone = firstRow.cloneNode(true);
    clone.querySelectorAll("input").forEach(function (input) {
      input.value = "";
    });
    var cloneSelect = clone.querySelector("select[name='treatment_catalog_id[]']");
    if (cloneSelect) {
      cloneSelect.value = "";
    }
    wireRow(clone);
    container.appendChild(clone);
  });
})();
