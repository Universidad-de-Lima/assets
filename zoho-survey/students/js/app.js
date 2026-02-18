(() => {
  'use strict';

  // ==================== CONSTANTES GLOBALES ====================
  const BASE_URL = 'https://Universidad-de-Lima.github.io/assets/zoho-survey/students/output';
  const META_NPS = 50;
  const META_CSAT = 93;
  const CARRERAS_12_CICLOS = ['Derecho', 'Psicología'];
  const FACULTADES_12_CICLOS = ['Facultad de Derecho', 'Facultad de Psicología'];
  const PROGRAMA_ESTUDIOS_GENERALES = 'Programa de Estudios Generales';
  const CICLOS_ESTUDIOS_GENERALES = ['1° Ciclo', '2° Ciclo'];
  const SAT_KEYS = ['Totalmente satisfecho', 'Muy satisfecho', 'Satisfecho', 'Insatisfecho', 'Totalmente insatisfecho'];
  const SAT_TOP3_KEYS = SAT_KEYS.slice(0, 3);

  // ==================== CACHÉ DE DATOS ====================
  const cache = {
    dashboard: null,
    dimensiones: null,
    ids: null,
    nps_ciclo_carrera: null,
    csat_ciclo_carrera: null,
    nps_carrera: null,
    csat_carrera: null,
    filtros: null
  };

  // ==================== REFERENCIAS AL DOM ====================
  const DOM = {
    tooltip:            document.getElementById('tooltip'),
    headerTitle:        document.getElementById('header-title'),
    footerAnio:         document.getElementById('footer-anio'),
    footerPeriodo:      document.getElementById('footer-periodo'),
    kpiNpsValue:        document.getElementById('kpi-nps-value'),
    kpiNpsBar:          document.getElementById('kpi-nps-bar'),
    kpiNpsMeta:         document.getElementById('kpi-nps-meta'),
    kpiCsatValue:       document.getElementById('kpi-csat-value'),
    kpiCsatBar:         document.getElementById('kpi-csat-bar'),
    kpiCsatMeta:        document.getElementById('kpi-csat-meta'),
    kpiDiasValue:       document.getElementById('kpi-dias-value'),
    kpiDiasBar:         document.getElementById('kpi-dias-bar'),
    kpiDiasMeta:        document.getElementById('kpi-dias-meta'),
    npsBar:             document.getElementById('nps-bar'),
    npsLegend:          document.getElementById('nps-legend'),
    csatBar:            document.getElementById('csat-bar'),
    csatLegend:         document.getElementById('csat-legend'),
    insightHallazgos:   document.getElementById('insight-hallazgos'),
    insightFortaleza:   document.getElementById('insight-fortaleza'),
    insightAtencion:    document.getElementById('insight-atencion'),
    radarChart:         document.getElementById('radar-chart'),
    detallePromedioRef: document.getElementById('detalle-promedio-ref'),
    progressFill:       document.getElementById('progress-fill')
  };

  let csatScoreGlobal = 0;

  // ==================== FUNCIONES AUXILIARES ====================
  const $ = (id) => document.getElementById(id);
  const $$ = (sel) => document.querySelectorAll(sel);

  // Formato de números
  const formatInteger = (n) => n.toString();

  const formatDecimal = (n, digits = 2) => {
    if (n === null || n === undefined) return '';
    const rounded = n.toFixed(digits);
    if (rounded.endsWith('0'.repeat(digits))) {
      return Math.round(n).toString();
    }
    return rounded.replace('.', ',');
  };

  const formatPercent = (n, digits = 2) => {
    const formatted = formatDecimal(n, digits);
    return formatted + ' %';
  };

  const formatPctSimple = (v, t) => {
    if (t === 0) return '0 %';
    return Math.round((v / t) * 100) + ' %';
  };

  const formatPctDecimal = (v, t) => {
    if (t === 0) return '0,0 %';
    const val = (v / t) * 100;
    return formatDecimal(val, 1) + ' %';
  };

  // Formato de nombre de dimensión con HTML (para visualización)
  const formatDimensionName = (dim) => {
    if (dim === 'Software especializado empleado en la carrera') {
      // Usamos etiqueta <i> para cursiva, evitando problemas de copiado
      return '<span><i>Software</i> especializado empleado en la carrera</span>';
    }
    if (dim === 'Portal web de la Universidad (MiUlima)') {
      return 'Portal web de la Universidad (Mi Ulima)';
    }
    if (dim === 'Conexión WiFi en el campus') {
      return 'Conexión Wi-Fi en el campus';
    }
    return dim;
  };


  // Fechas: mes completo y sin año
  const formatDate = (ds) =>
    new Date(`${ds}T12:00:00`).toLocaleDateString('es-PE', { day: 'numeric', month: 'long' });

  // Cálculos simples
  const pct = (v, t) => t > 0 ? Math.round((v / t) * 100) : 0;
  const pct2 = (v, t) => t > 0 ? ((v / t) * 100).toFixed(1) : '0.0';
  const esEstudiosGenerales = (facultad) => facultad === PROGRAMA_ESTUDIOS_GENERALES;
  const cortarTexto = (texto, max) => texto.length > max ? `${texto.slice(0, max - 1)}…` : texto;
  const sumKeys = (row, keys) => keys.reduce((acc, k) => acc + (row[k] || 0), 0);

  // Filtrado de datos
  function filtrarDatos(datos, fac, car, cic) {
    return datos.filter(r => {
      if (esEstudiosGenerales(fac)) {
        return CICLOS_ESTUDIOS_GENERALES.includes(r.ciclo) &&
               (!car || r.carrera === car) &&
               (!cic || r.ciclo === cic);
      }
      return (!fac || r.facultad === fac) &&
             (!car || r.carrera === car) &&
             (!cic || r.ciclo === cic);
    });
  }

  function getCiclosForFiltro(facultad, carrera) {
    if (esEstudiosGenerales(facultad)) return CICLOS_ESTUDIOS_GENERALES;
    const maxCiclo = (FACULTADES_12_CICLOS.includes(facultad) || CARRERAS_12_CICLOS.includes(carrera)) ? 12 : 10;
    return cache.filtros.ciclos.filter(c => (parseInt(c) || 0) <= maxCiclo);
  }

  const ordenarFacultades = (lista) => [PROGRAMA_ESTUDIOS_GENERALES, ...lista.sort()];

  // Tooltips (sin transformación automática)
  const showTooltip = (e, content) => {
    const { tooltip } = DOM;
    tooltip.innerHTML = content;
    tooltip.style.display = 'block';
    tooltip.style.left = `${e.pageX + 10}px`;
    tooltip.style.top = `${e.pageY - 10}px`;
  };

  const hideTooltip = () => {
    DOM.tooltip.style.display = 'none';
  };

  window.showTooltip = showTooltip;
  window.hideTooltip = hideTooltip;

  function addTooltipToSegments(selector) {
    $$(selector).forEach(seg => {
      seg.addEventListener('mousemove', (e) =>
        showTooltip(e, `${seg.dataset.label}: ${seg.dataset.value}`)
      );
      seg.addEventListener('mouseleave', hideTooltip);
    });
  }

  // Formato para textos de ciclo en selects (con superíndices)
  const formatCicloText = (ciclo) => {
    const match = ciclo.match(/^(\d+)/);
    if (!match) return ciclo;
    const num = match[1];
    if (num === '1' || num === '3') {
      return `${num}.ᵉʳ ciclo`;
    }
    return `${num}.º ciclo`;
  };

  // Poblado de selects con opciones personalizadas
  function populateSelect(sel, placeholder, items, texts) {
    const current = sel.value;
    sel.innerHTML = `<option value="">${placeholder}</option>`;
    items.forEach((item, index) => {
      const opt = document.createElement('option');
      opt.value = item;
      opt.textContent = texts ? texts[index] : item;
      sel.appendChild(opt);
    });
    if (items.includes(current)) sel.value = current;
  }

  // ==================== CARGA DE DATOS ====================
  async function loadAllData() {
    try {
      const endpoints = [
        'dashboard_data', 'dimensiones', 'ids',
        'nps_ciclo_carrera', 'csat_ciclo_carrera',
        'nps_carrera', 'csat_carrera', 'filtros'
      ];
      const results = await Promise.all(
        endpoints.map(name => fetch(`${BASE_URL}/${name}.json`).then(r => r.json()))
      );
      const [dashboard, dimensiones, ids, nps_cc, csat_cc, nps_car, csat_car, filtros] = results;
      Object.assign(cache, {
        dashboard, dimensiones, ids,
        nps_ciclo_carrera: nps_cc,
        csat_ciclo_carrera: csat_cc,
        nps_carrera: nps_car,
        csat_carrera: csat_car,
        filtros
      });
      csatScoreGlobal = dashboard.resumen.csat.score;
      return true;
    } catch (error) {
      console.error('Error cargando datos:', error);
      return false;
    }
  }

  // ==================== SECCIÓN EJECUTIVO ====================
  function renderEjecutivo() {
    const { resumen: r, hallazgos: h, nps, csat } = cache.dashboard;
    DOM.headerTitle.textContent = `Encuesta de Satisfacción Estudiantil ${r.año}`;
    DOM.footerAnio.textContent = r.año;
    DOM.footerPeriodo.textContent =
      `Período: ${formatDate(r.fecha_inicio)} - ${formatDate(r.fecha_fin)} · Dirección de Planificación y Acreditación`;

    DOM.kpiNpsValue.textContent = formatDecimal(r.nps.score);
    DOM.kpiNpsBar.style.width = `${Math.min(100, Math.max(0, r.nps.score))}%`;
    DOM.kpiNpsMeta.textContent = `Meta ${formatInteger(META_NPS)}`;

    DOM.kpiCsatValue.textContent = formatPercent(r.csat.score);
    DOM.kpiCsatBar.style.width = `${r.csat.score}%`;
    DOM.kpiCsatMeta.textContent = `Meta ${formatPercent(META_CSAT)}`;

    DOM.kpiDiasValue.textContent = formatInteger(r.dias_recoleccion);
    DOM.kpiDiasBar.style.width = `${(r.dias_recoleccion / r.dias) * 100}%`;
    DOM.kpiDiasMeta.textContent = `${formatDate(r.fecha_inicio)} - ${formatDate(r.fecha_fin)}`;

    renderNPSBar(nps);
    renderCSATBar(csat);

    const { nps_etapas: etapas } = h;
    DOM.insightHallazgos.innerHTML = `
      Actualmente <strong>+${formatInteger(h.csat_pct)} %</strong> de estudiantes están satisfechos con la Universidad de Lima.
      El Índice de Promotores Netos que es de <strong>+${formatInteger(h.nps_score)}</strong>, posiciona a la institución en el rango
      "<strong>${h.nps_tipo}</strong>" a nivel global,
      pero <strong>${h.tendencia}</strong> conforme avanza la carrera:
      <strong>Inicial (${formatDecimal(etapas.Inicial || 0)})</strong> →
      <strong>Intermedio (${formatDecimal(etapas.Intermedio || 0)})</strong> →
      <strong>Avanzado (${formatDecimal(etapas.Avanzado || 0)})</strong>.
      Teniendo una diferencia de <strong>-${formatInteger(h.delta)}</strong> puntos en el ciclo de vida estudiantil.
    `;
  }

  function renderNPSBar(nps) {
    const total = nps.Promotores + nps.Pasivos + nps.Detractores;
    DOM.npsBar.innerHTML = `
      <div class="csat-segment" style="width:${pct(nps.Promotores, total)}%; background:var(--gray-700);"
           data-label="Promotores (9-10)" data-value="${formatInteger(nps.Promotores)} (${formatPctDecimal(nps.Promotores, total)})">${formatPctSimple(nps.Promotores, total)}</div>
      <div class="csat-segment" style="width:${pct(nps.Pasivos, total)}%; background:var(--gray-400);"
           data-label="Pasivos (7-8)" data-value="${formatInteger(nps.Pasivos)} (${formatPctDecimal(nps.Pasivos, total)})">${formatPctSimple(nps.Pasivos, total)}</div>
      <div class="csat-segment" style="width:${pct(nps.Detractores, total)}%; background:var(--ulima-orange);"
           data-label="Detractores (0-6)" data-value="${formatInteger(nps.Detractores)} (${formatPctDecimal(nps.Detractores, total)})">${formatPctSimple(nps.Detractores, total)}</div>
    `;
    DOM.npsLegend.innerHTML = `
      <div class="legend-item"><div class="legend-dot" style="background:var(--gray-700);"></div>Promotores: ${formatInteger(nps.Promotores)}</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--gray-400);"></div>Pasivos: ${formatInteger(nps.Pasivos)}</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--ulima-orange);"></div>Detractores: ${formatInteger(nps.Detractores)}</div>
    `;
    addTooltipToSegments('#nps-bar .csat-segment');
  }

  function renderCSATBar(csat) {
    const labels = [
      { key: 'Totalmente satisfecho', color: 'var(--gray-900)' },
      { key: 'Muy satisfecho',        color: 'var(--gray-600)' },
      { key: 'Satisfecho',            color: 'var(--gray-400)' },
      { key: 'Insatisfecho',          color: 'var(--ulima-orange)' },
      { key: 'Totalmente insatisfecho', color: 'var(--ulima-red)' }
    ];
    const total = labels.reduce((sum, l) => sum + (csat[l.key] || 0), 0);
    const visibleLabels = labels.filter(l => csat[l.key] > 0);
    DOM.csatBar.innerHTML = visibleLabels.map(l => {
      const p = pct(csat[l.key], total);
      return `<div class="csat-segment" style="width:${p}%; background:${l.color};"
              data-label="${l.key}" data-value="${formatInteger(csat[l.key])} (${formatPctDecimal(csat[l.key], total)})">${p < 2 ? '' : formatPctSimple(csat[l.key], total)}</div>`;
    }).join('');
    DOM.csatLegend.innerHTML = visibleLabels.map(l =>
      `<div class="legend-item"><div class="legend-dot" style="background:${l.color};"></div>${l.key}: ${formatInteger(csat[l.key])}</div>`
    ).join('');
    addTooltipToSegments('#csat-bar .csat-segment');
  }

  // ==================== SECCIÓN OPERATIVO ====================
  function dimensionAplica(rows, dimension) {
    return rows.some(r => r.dimension === dimension && sumKeys(r, SAT_KEYS) > 0);
  }

  // Gráficos de barras Top 3
  function renderTop3Bars(containerId, data) {
    const container = $(containerId);
    const fragment = document.createDocumentFragment();
    data.forEach((item, idx) => {
      const barClass = item.pct >= 90 ? 'high' : item.pct >= 80 ? 'medium' : 'low';
      const barItem = document.createElement('div');
      barItem.className = 'bar-item';
      const pctFormatted = formatPercent(item.pct, 2);
      const dimFormatted = formatDimensionName(item.dim);
      barItem.innerHTML = `
        <div class="bar-label">${dimFormatted}</div>
        <div class="bar-container">
          <div class="bar-fill animated ${barClass}" style="width:${item.pct}%; animation-delay:${idx * 0.08}s">
            <span class="bar-value">${pctFormatted}</span>
          </div>
        </div>
      `;
      const barContainer = barItem.querySelector('.bar-container');
      barContainer.addEventListener('mousemove', (e) => {
        const fac = $('filter-facultad-top3').value;
        const car = $('filter-carrera-top3').value;
        const cic = $('filter-ciclo-top3').value;
        const rows = filtrarDatos(cache.dimensiones, fac, car, cic).filter(r => r.dimension === item.dim);
        const conteos = {
          'Totalmente satisfecho': 0, 'Muy satisfecho': 0, 'Satisfecho': 0,
          'Insatisfecho': 0, 'Totalmente insatisfecho': 0, 'No utilizo': 0, 'No conozco': 0
        };
        rows.forEach(r => Object.keys(conteos).forEach(k => { conteos[k] += r[k] || 0; }));
        const lines = Object.entries(conteos).filter(([, v]) => v > 0).map(([k, v]) => `${k}: ${formatInteger(v)}`);
        if (lines.length === 0) return hideTooltip();
        showTooltip(e, lines.join('<br>'));
      });
      barContainer.addEventListener('mouseleave', hideTooltip);
      fragment.appendChild(barItem);
    });
    container.innerHTML = '';
    container.appendChild(fragment);
  }

  function updateTop3Filters() {
    const fac = $('filter-facultad-top3').value;
    const car = $('filter-carrera-top3').value;
    const cic = $('filter-ciclo-top3').value;
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const categorias = {
      academico: 'Académico',
      infraestructura: 'Infraestructura',
      tecnologia: 'Tecnología',
      adminBienestar: 'Administrativo y Bienestar'
    };
    const top3Data = {};
    Object.entries(categorias).forEach(([key, nombre]) => {
      const dims = {};
      filtered.filter(r => r.categoria === nombre).forEach(r => {
        if (!dimensionAplica(filtered, r.dimension)) return;
        if (!dims[r.dimension]) dims[r.dimension] = { total: 0, top3: 0 };
        const total = sumKeys(r, SAT_KEYS);
        const top3 = sumKeys(r, SAT_TOP3_KEYS);
        dims[r.dimension].total += total;
        dims[r.dimension].top3 += top3;
      });
      top3Data[key] = Object.entries(dims)
        .map(([dim, v]) => ({ dim, pct: v.total ? (v.top3 / v.total) * 100 : 0, categoria: nombre }))
        .sort((a, b) => b.pct - a.pct);
    });
    renderTop3Bars('chart-academico', top3Data.academico);
    renderTop3Bars('chart-infraestructura', top3Data.infraestructura);
    renderTop3Bars('chart-tecnologia', top3Data.tecnologia);
    renderTop3Bars('chart-admin-bienestar', top3Data.adminBienestar);
  }

  // Gráfico radar
  function renderRadarIndependiente() {
    const fac = $('filter-facultad-radar').value;
    const car = $('filter-carrera-radar').value;
    const cic = $('filter-ciclo-radar').value;
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const dims = {};
    filtered.forEach(r => {
      if (!dimensionAplica(filtered, r.dimension)) return;
      if (!dims[r.dimension]) dims[r.dimension] = { total: 0, top3: 0, categoria: r.categoria };
      dims[r.dimension].total += sumKeys(r, SAT_KEYS);
      dims[r.dimension].top3 += sumKeys(r, SAT_TOP3_KEYS);
    });
    const allDims = Object.entries(dims)
      .filter(([, v]) => v.total > 0)
      .map(([dim, v]) => ({ dim, pct: (v.top3 / v.total) * 100, categoria: v.categoria }));
    if (allDims.length === 0) {
      DOM.radarChart.innerHTML = '<text x="300" y="250" text-anchor="middle">Sin datos</text>';
      updateInsightFortaleza([], fac, car, cic);
      return;
    }
    allDims.sort((a, b) => b.pct - a.pct);
    const cx = 300, cy = 250, maxR = 200;
    const n = allDims.length;
    const svgParts = [];
    [0.25, 0.5, 0.75, 1].forEach(f => {
      svgParts.push(`<circle cx="${cx}" cy="${cy}" r="${maxR * f}" fill="none" stroke="#E5E7EB" stroke-width="1"/>`);
    });
    allDims.forEach((d, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const x2 = cx + maxR * Math.cos(angle);
      const y2 = cy + maxR * Math.sin(angle);
      svgParts.push(`<line x1="${cx}" y1="${cy}" x2="${x2}" y2="${y2}" stroke="#E5E7EB" stroke-width="1"/>`);
      const labelOffset = 26;
      const lx = cx + (maxR + labelOffset) * Math.cos(angle);
      const ly = cy + (maxR + labelOffset) * Math.sin(angle);
      const anchor = (angle > Math.PI / 2 || angle < -Math.PI / 2) ? 'end' : 'start';
      const dimFormatted = formatDimensionName(d.dim);
      svgParts.push(`<text x="${lx}" y="${ly}" font-size="10" font-weight="500" fill="#6B7280" text-anchor="${anchor}"
                dominant-baseline="middle" onmousemove="showTooltip(event, '${d.dim}')" onmouseleave="hideTooltip()">${cortarTexto(dimFormatted.replace(/<[^>]*>/g, ''), 26)}</text>`);
    });
    const outerPoints = allDims.map((d, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      return `${cx + maxR * Math.cos(angle)},${cy + maxR * Math.sin(angle)}`;
    }).join(' ');
    const dataPoints = allDims.map((d, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const r = (d.pct / 100) * maxR;
      return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
    }).join(' ');
    svgParts.push(`<polygon points="${outerPoints}" fill="rgba(55,65,81,0.18)" stroke="#374151" stroke-width="2">
      <animate attributeName="points" from="${outerPoints}" to="${dataPoints}" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
    </polygon>`);
    allDims.forEach((d, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const rFinal = (d.pct / 100) * maxR;
      const ox = cx + maxR * Math.cos(angle);
      const oy = cy + maxR * Math.sin(angle);
      const px = cx + rFinal * Math.cos(angle);
      const py = cy + rFinal * Math.sin(angle);
      const color = d.pct >= 90 ? '#374151' : d.pct >= 80 ? '#9CA3AF' : '#FF0000';
      const pctFormatted = formatPercent(d.pct, 2);
      const dimTooltip = d.dim;
      svgParts.push(`<circle cx="${ox}" cy="${oy}" r="4" fill="${color}" style="cursor:pointer; opacity:0"
                onmousemove="showTooltip(event, '${dimTooltip}: ${pctFormatted}')" onmouseleave="hideTooltip()">
                <animate attributeName="cx" from="${ox}" to="${px}" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
                <animate attributeName="cy" from="${oy}" to="${py}" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
                <animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="0.5s" fill="freeze"/>
              </circle>`);
    });
    DOM.radarChart.innerHTML = svgParts.join('');
    setTimeout(() => {
      DOM.radarChart.querySelectorAll('animate').forEach(anim => {
        try { anim.beginElement(); } catch {  }
      });
    }, 10);
    updateInsightFortaleza(allDims, fac, car, cic);
  }

  function updateInsightFortaleza(allDims, fac, car, cic) {
    if (!DOM.insightFortaleza || allDims.length === 0) {
      if (DOM.insightFortaleza) DOM.insightFortaleza.innerHTML = 'Sin datos suficientes para el análisis.';
      return;
    }
    const fortalezas = allDims.filter(d => d.pct >= 90).sort((a, b) => b.pct - a.pct);
    const adecuados  = allDims.filter(d => d.pct >= 80 && d.pct < 90).sort((a, b) => b.pct - a.pct);
    const atencion   = allDims.filter(d => d.pct < 80).sort((a, b) => a.pct - b.pct);
    const hayFiltro  = fac || car || cic;
    const contexto   = hayFiltro ? [fac, car, cic].filter(Boolean).join(' · ') : '';
    let narrativa    = '';
    const fmtPct = (val) => formatPercent(val, 2);
    const fmtDim = (dim) => formatDimensionName(dim);
    if (hayFiltro) {
      narrativa += `<strong style="font-size:11px; text-transform:uppercase; letter-spacing:0.5px;">${contexto}</strong><br>`;
      if (fortalezas.length > 0) {
        const top = fortalezas.slice(0, 3);
        narrativa += `${fortalezas.length === 1 ? 'La dimensión mejor evaluada es' : 'Las dimensiones mejor evaluadas son'} `;
        narrativa += top.map(d => `<strong>${fmtDim(d.dim)}</strong> (${fmtPct(d.pct)})`).join(', ');
        narrativa += `. En total, <strong>${fortalezas.length}</strong> de ${allDims.length} dimensiones superan el 90% de satisfacción.`;
      } else {
        narrativa += `Ninguna dimensión alcanza el umbral de <strong>90%</strong> (Fortaleza). `;
        if (adecuados.length > 0) {
          const topAd = adecuados.slice(0, 2);
          narrativa += `Las más cercanas son ${topAd.map(d => `<strong>${fmtDim(d.dim)}</strong> (${fmtPct(d.pct)})`).join(' y ')}.`;
        }
      }
      if (atencion.length > 0) {
        narrativa += ` ${atencion.length === 1 ? 'Requiere' : 'Requieren'} atención: `;
        narrativa += atencion.slice(0, 2).map(d => `<strong>${fmtDim(d.dim)}</strong> (${fmtPct(d.pct)})`).join(' y ');
        narrativa += ` por estar debajo del 80%.`;
      }
    } else {
      if (fortalezas.length > 0) {
        const top = fortalezas.slice(0, 2);
        narrativa += `La satisfacción en ${top.map(d => `<strong>${fmtDim(d.dim)}</strong> (${fmtPct(d.pct)})`).join(' y ')} son las mejor evaluadas. `;
        narrativa += `En total, <strong>${fortalezas.length}</strong> de ${allDims.length} dimensiones se encuentran en rango de Fortaleza (≥90%).`;
      } else {
        narrativa += `Actualmente ninguna dimensión alcanza el umbral de <strong>90%</strong> (Fortaleza).`;
      }
      if (atencion.length > 0) {
        narrativa += ` ${atencion.length === 1 ? 'La dimensión' : 'Las dimensiones'} `;
        narrativa += atencion.slice(0, 2).map(d => `<strong>${fmtDim(d.dim)}</strong> (${fmtPct(d.pct)})`).join(' y ');
        narrativa += ` ${atencion.length === 1 ? 'requiere' : 'requieren'} atención prioritaria.`;
      }
    }
    DOM.insightFortaleza.innerHTML = narrativa;
  }

  // ==================== SECCIÓN ANALÍTICO ====================
  // Tabla de preguntas detalladas
  function renderPreguntas() {
    const fac = $('filter-facultad-preguntas').value;
    const car = $('filter-carrera-preguntas').value;
    const cic = $('filter-ciclo-preguntas').value;
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const dimMap = {};
    filtered.forEach(r => {
      if (!dimMap[r.dimension]) {
        dimMap[r.dimension] = { categoria: r.categoria, totSat: 0, muySat: 0, sat: 0, insat: 0, totInsat: 0 };
      }
      dimMap[r.dimension].totSat   += r['Totalmente satisfecho'] || 0;
      dimMap[r.dimension].muySat   += r['Muy satisfecho'] || 0;
      dimMap[r.dimension].sat      += r['Satisfecho'] || 0;
      dimMap[r.dimension].insat    += r['Insatisfecho'] || 0;
      dimMap[r.dimension].totInsat += r['Totalmente insatisfecho'] || 0;
    });
    const data = Object.entries(dimMap).map(([dim, v]) => {
      const total = v.totSat + v.muySat + v.sat + v.insat + v.totInsat;
      const top3  = v.totSat + v.muySat + v.sat;
      const p1 = total > 0 ? Math.round((v.totSat   / total) * 100) : 0;
      const p2 = total > 0 ? Math.round((v.muySat   / total) * 100) : 0;
      const p3 = total > 0 ? Math.round((v.sat      / total) * 100) : 0;
      const p4 = total > 0 ? Math.round((v.insat    / total) * 100) : 0;
      const p5 = total > 0 ? Math.max(0, 100 - p1 - p2 - p3 - p4)  : 0;
      return {
        dimension: dim, categoria: v.categoria,
        top3box: total > 0 ? ((top3 / total) * 100).toFixed(2) : '0.00',
        totSat: v.totSat, muySat: v.muySat, sat: v.sat, insat: v.insat, totInsat: v.totInsat,
        total, pctTotSat: p1, pctMuySat: p2, pctSat: p3, pctInsat: p4, pctTotInsat: p5
      };
    }).filter(item => parseFloat(item.top3box) > 0).sort((a, b) => parseFloat(b.top3box) - parseFloat(a.top3box));
    const tbody = $('tbody-preguntas');
    const fragment = document.createDocumentFragment();
    data.forEach(item => {
      const tr = document.createElement('tr');
      const catCorta = item.categoria === 'Administrativo y Bienestar' ? 'Bienestar' : item.categoria;
      const heatClass = parseFloat(item.top3box) >= 90 ? 'heat-high' : parseFloat(item.top3box) >= 80 ? 'heat-medium' : 'heat-low';
      const top3boxFormatted = formatPercent(parseFloat(item.top3box), 2);
      const dimFormatted = formatDimensionName(item.dimension);
      tr.innerHTML = `
        <td>${dimFormatted}</td>
        <td class="text-center"><span class="heatmap-cell ${heatClass}">${top3boxFormatted}</span></td>
        <td class="text-center">${catCorta}</td>
        <td>
          <div class="distribution-bar animated">
            <div class="distribution-segment" style="width:${item.pctTotSat}%; background: var(--gray-800);" data-label="Totalmente satisfecho" data-value="${formatInteger(item.totSat)}">${item.pctTotSat < 3 ? '' : formatInteger(item.pctTotSat) + ' %'}</div>
            <div class="distribution-segment" style="width:${item.pctMuySat}%; background: var(--gray-500);" data-label="Muy satisfecho" data-value="${formatInteger(item.muySat)}">${item.pctMuySat < 3 ? '' : formatInteger(item.pctMuySat) + ' %'}</div>
            <div class="distribution-segment" style="width:${item.pctSat}%; background: var(--gray-300); color: var(--gray-700);" data-label="Satisfecho" data-value="${formatInteger(item.sat)}">${item.pctSat < 3 ? '' : formatInteger(item.pctSat) + ' %'}</div>
            <div class="distribution-segment" style="width:${item.pctInsat}%; background: var(--ulima-orange);" data-label="Insatisfecho" data-value="${formatInteger(item.insat)}">${item.pctInsat < 3 ? '' : formatInteger(item.pctInsat) + ' %'}</div>
            <div class="distribution-segment" style="width:${item.pctTotInsat}%; background: var(--ulima-red);" data-label="Totalmente insatisfecho" data-value="${formatInteger(item.totInsat)}">${item.pctTotInsat < 3 ? '' : formatInteger(item.pctTotInsat) + ' %'}</div>
          </div>
        </td>
      `;
      tr.querySelectorAll('.distribution-segment').forEach(seg => {
        seg.addEventListener('mousemove', e =>
          showTooltip(e, `${seg.dataset.label}: ${formatInteger(parseInt(seg.dataset.value))}`)
        );
        seg.addEventListener('mouseleave', hideTooltip);
      });
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);
  }

  // Tabla de detalle por carrera
  function renderDetalleCarreras() {
    const fac = $('filter-facultad-detalle').value;
    const cic = $('filter-ciclo-detalle').value;
    const filteredIds = filtrarDatos(cache.ids, fac, null, cic);
    const conteo = {};
    filteredIds.forEach(r => { conteo[r.carrera] = (conteo[r.carrera] || 0) + r.count; });
    const npsMap = {};
    filtrarDatos(cache.nps_ciclo_carrera, fac, null, cic).forEach(r => {
      if (!npsMap[r.carrera]) npsMap[r.carrera] = { prom: 0, pas: 0, det: 0 };
      npsMap[r.carrera].prom += r.Promotores;
      npsMap[r.carrera].pas  += r.Pasivos || 0;
      npsMap[r.carrera].det  += r.Detractores;
    });
    const csatMap = {};
    filtrarDatos(cache.csat_ciclo_carrera, fac, null, cic).forEach(r => {
      if (!csatMap[r.carrera]) csatMap[r.carrera] = { t3b: 0, total: 0 };
      const t3b   = sumKeys(r, SAT_TOP3_KEYS);
      const total = t3b + (r['Insatisfecho'] || 0) + (r['Totalmente insatisfecho'] || 0);
      csatMap[r.carrera].t3b   += t3b;
      csatMap[r.carrera].total += total;
    });
    let csatPromedioReferencia = csatScoreGlobal;
    if (esEstudiosGenerales(fac)) {
      let totalT3b = 0, totalResp = 0;
      Object.values(csatMap).forEach(v => { totalT3b += v.t3b; totalResp += v.total; });
      csatPromedioReferencia = totalResp > 0 ? (totalT3b / totalResp) * 100 : csatScoreGlobal;
    }
    DOM.detallePromedioRef.textContent = `(${formatDecimal(csatPromedioReferencia, 2)} %)`;
    const data = Object.entries(conteo).map(([carrera, encuestas]) => {
      const nps = npsMap[carrera];
      const csat = csatMap[carrera];
      const npsTotal = nps ? (nps.prom + nps.pas + nps.det) : 0;
      const npsScore = npsTotal > 0 ? ((nps.prom - nps.det) / npsTotal) * 100 : 0;
      const csatScore = csat?.total > 0 ? (csat.t3b / csat.total) * 100 : 0;
      return { carrera, encuestas, nps: npsScore, csat: csatScore, vsProm: csatScore - csatPromedioReferencia };
    }).sort((a, b) => a.carrera.localeCompare(b.carrera));
    const tbody = $('tbody-detalle');
    const fragment = document.createDocumentFragment();
    data.forEach(item => {
      const tr = document.createElement('tr');
      const vsProm = item.vsProm >= 0
        ? `<span style="color: #00B04F; font-weight: 600;">+${formatDecimal(item.vsProm, 2)}</span>`
        : `<span style="color: #FF0000; font-weight: 600;">${formatDecimal(item.vsProm, 2)}</span>`;
      tr.innerHTML = `
        <td>${item.carrera}</td>
        <td class="text-center">${formatInteger(item.encuestas)}</td>
        <td class="text-center" style="font-weight: 700;">${formatDecimal(item.nps, 2)}</td>
        <td class="text-center">${formatPercent(item.csat, 2)}</td>
        <td class="text-center">${vsProm}</td>
      `;
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);
  }

  // Tabla de visibilidad de servicios
  function renderVisibilidad() {
    const fac = $('filter-facultad-visibilidad').value;
    const car = $('filter-carrera-visibilidad').value;
    const cic = $('filter-ciclo-visibilidad').value;
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const dimMap = {};
    filtered.forEach(r => {
      if (!dimMap[r.dimension]) dimMap[r.dimension] = { noConozco: 0, noUtilizo: 0, conoce: 0 };
      dimMap[r.dimension].noConozco += r['No conozco'] || 0;
      dimMap[r.dimension].noUtilizo += r['No utilizo'] || 0;
      dimMap[r.dimension].conoce    += sumKeys(r, SAT_KEYS);
    });
    const data = Object.entries(dimMap)
      .filter(([, v]) => v.noConozco > 0 || v.noUtilizo > 0)
      .map(([dim, v]) => {
        const total = v.noConozco + v.noUtilizo + v.conoce;
        return {
          dimension: dim,
          noConozco: v.noConozco,
          noUtilizo: v.noUtilizo,
          conoce: v.conoce,
          pctNoConozco: total > 0 ? (v.noConozco / total) * 100 : 0,
          pctNoUtilizo: total > 0 ? (v.noUtilizo / total) * 100 : 0,
          pctConoce:    total > 0 ? (v.conoce    / total) * 100 : 0,
          total
        };
      })
      .sort((a, b) => (a.pctNoConozco + a.pctNoUtilizo) - (b.pctNoConozco + b.pctNoUtilizo));
    const tbody = $('tbody-visibilidad');
    const fragment = document.createDocumentFragment();
    const fmtVisibilidad = v => v < 6.5 ? '' : formatDecimal(v, 2) + ' %';
    data.forEach(item => {
      const tr = document.createElement('tr');
      const dimFormatted = formatDimensionName(item.dimension);
      tr.innerHTML = `
        <td>${dimFormatted}</td>
        <td class="text-center">${formatInteger(item.noConozco)} (${formatDecimal(item.pctNoConozco, 2)} %)</td>
        <td class="text-center">${formatInteger(item.noUtilizo)} (${formatDecimal(item.pctNoUtilizo, 2)} %)</td>
        <td>
          <div class="visibility-bar animated">
            <div class="visibility-segment no-conozco" style="width:${item.pctNoConozco}%;" data-label="No conozco" data-value="${formatInteger(item.noConozco)}">${fmtVisibilidad(item.pctNoConozco)}</div>
            <div class="visibility-segment no-utilizo" style="width:${item.pctNoUtilizo}%;" data-label="No utilizo" data-value="${formatInteger(item.noUtilizo)}">${fmtVisibilidad(item.pctNoUtilizo)}</div>
            <div class="visibility-segment conocido" style="width:${item.pctConoce}%;" data-label="Conoce/Utiliza" data-value="${formatInteger(item.conoce)}">${fmtVisibilidad(item.pctConoce)}</div>
          </div>
        </td>
      `;
      tr.querySelectorAll('.visibility-segment').forEach(seg => {
        seg.addEventListener('mousemove', e =>
          showTooltip(e, `${seg.dataset.label}: ${formatInteger(parseInt(seg.dataset.value))}`)
        );
        seg.addEventListener('mouseleave', hideTooltip);
      });
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);
    updateInsightAtencion(data, fac, car, cic);
  }

  function updateInsightAtencion(data, fac, car, cic) {
    if (!DOM.insightAtencion || data.length === 0) {
      if (DOM.insightAtencion) DOM.insightAtencion.innerHTML = 'Sin datos suficientes para el análisis.';
      return;
    }
    const sorted    = [...data].sort((a, b) => (b.pctNoConozco + b.pctNoUtilizo) - (a.pctNoConozco + a.pctNoUtilizo));
    const criticos  = sorted.filter(d => (d.pctNoConozco + d.pctNoUtilizo) >= 50);
    const moderados = sorted.filter(d => {
      const comb = d.pctNoConozco + d.pctNoUtilizo;
      return comb >= 25 && comb < 50;
    });
    const hayFiltro = fac || car || cic;
    const contexto  = hayFiltro ? [fac, car, cic].filter(Boolean).join(' · ') : '';
    let narrativa   = '';
    const fmtPct = (val) => formatDecimal(val, 2) + ' %';
    const fmtDim = (dim) => formatDimensionName(dim);
    if (hayFiltro) {
      narrativa += `<strong style="font-size:11px; text-transform:uppercase; letter-spacing:0.5px;">${contexto}</strong><br>`;
      if (criticos.length > 0) {
        const top = criticos.slice(0, 3);
        narrativa += `${criticos.length === 1 ? 'El servicio con menor visibilidad es' : 'Los servicios con menor visibilidad son'} `;
        narrativa += top.map(d => `<strong>${fmtDim(d.dimension)}</strong> (${fmtPct(d.pctNoConozco)} No conozco + ${fmtPct(d.pctNoUtilizo)} No utilizo)`).join(', ');
        narrativa += `. En total, <strong>${criticos.length}</strong> de ${data.length} dimensiones tienen más del 50% de desconocimiento o no uso.`;
      } else if (moderados.length > 0) {
        const top = moderados.slice(0, 2);
        narrativa += `No hay servicios con desconocimiento crítico (>50%). Las dimensiones con mayor oportunidad son `;
        narrativa += top.map(d => `<strong>${fmtDim(d.dimension)}</strong> (${fmtPct(d.pctNoConozco)} No conozco + ${fmtPct(d.pctNoUtilizo)} No utilizo)`).join(' y ');
        narrativa += `.`;
      } else {
        const top = sorted.slice(0, 2);
        narrativa += `Los servicios presentan niveles aceptables de visibilidad. Las dimensiones con mayor margen de mejora son `;
        narrativa += top.map(d => `<strong>${fmtDim(d.dimension)}</strong> (${fmtPct(d.pctNoConozco)} No conozco + ${fmtPct(d.pctNoUtilizo)} No utilizo)`).join(' y ');
        narrativa += `.`;
      }
    } else {
      if (sorted.length >= 2) {
        const [lowest, secondLowest] = sorted;
        narrativa += `<strong>${fmtDim(lowest.dimension)} (${fmtPct(lowest.pctNoConozco)} No conozco + ${fmtPct(lowest.pctNoUtilizo)} No utilizo)</strong> y `;
        narrativa += `<strong>${fmtDim(secondLowest.dimension)} (${fmtPct(secondLowest.pctNoConozco)} No conozco + ${fmtPct(secondLowest.pctNoUtilizo)} No utilizo)</strong> `;
        narrativa += `son las que presentan menor visibilidad.`;
        if (criticos.length > 0) {
          narrativa += ` En total, <strong>${criticos.length}</strong> de ${data.length} dimensiones superan el 50% de desconocimiento o no uso.`;
        }
      } else if (sorted.length === 1) {
        const [lowest] = sorted;
        narrativa += `<strong>${fmtDim(lowest.dimension)} (${fmtPct(lowest.pctNoConozco)} No conozco + ${fmtPct(lowest.pctNoUtilizo)} No utilizo)</strong> es la que presenta menor visibilidad.`;
      }
    }
    DOM.insightAtencion.innerHTML = narrativa;
  }

  // ==================== CONFIGURACIÓN DE FILTROS ====================
  function setupFilters(prefix, onChangeCallback) {
    const selFac = $(`filter-facultad-${prefix}`);
    const selCar = $(`filter-carrera-${prefix}`);
    const selCic = $(`filter-ciclo-${prefix}`);
    const { filtros } = cache;
    const syncActiveClass = () => {
      [selFac, selCar, selCic].forEach(sel => {
        if (sel) sel.classList.toggle('filter-active', sel.value !== '');
      });
    };
    ordenarFacultades(filtros.facultades).forEach(f => {
      const opt = document.createElement('option');
      opt.value = f;
      opt.textContent = f;
      selFac.appendChild(opt);
    });
    const updateCascade = () => {
      const facVal = selFac.value;
      if (selCar) {
        const carrerasBase = (facVal && !esEstudiosGenerales(facVal))
          ? filtros.facultad_carrera[facVal]
          : filtros.carreras;
        populateSelect(selCar, 'Todas las carreras', [...carrerasBase].sort());
      }
      const carVal = selCar?.value ?? '';
      if (selCic) {
        const ciclos = (facVal || carVal) ? getCiclosForFiltro(facVal, carVal) : filtros.ciclos;
        const ciclosText = ciclos.map(c => formatCicloText(c));
        populateSelect(selCic, 'Todos los ciclos', ciclos, ciclosText);
      }
      onChangeCallback?.();
      syncActiveClass();
    };
    selFac.addEventListener('change', updateCascade);
    selCar?.addEventListener('change', () => {
      if (selCic) {
        const facVal = selFac.value;
        const carVal = selCar.value;
        const ciclos = (facVal || carVal) ? getCiclosForFiltro(facVal, carVal) : cache.filtros.ciclos;
        const ciclosText = ciclos.map(c => formatCicloText(c));
        populateSelect(selCic, 'Todos los ciclos', ciclos, ciclosText);
      }
      onChangeCallback?.();
      syncActiveClass();
    });
    selCic?.addEventListener('change', () => {
      onChangeCallback?.();
      syncActiveClass();
    });
    const resetBtn = $(`reset-${prefix}`);
    resetBtn?.addEventListener('click', () => {
      selFac.value = '';
      if (selCar) selCar.value = '';
      if (selCic) selCic.value = '';
      updateCascade();
    });
    updateCascade();
  }

  // ==================== BARRA DE PROGRESO ====================
  function setupProgressBar() {
    let ticking = false;
    window.addEventListener('scroll', () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
          const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
          DOM.progressFill.style.width = `${(scrollTop / scrollHeight) * 100}%`;
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  }

  // ==================== INICIALIZACIÓN ====================
  async function init() {
    if (!await loadAllData()) {
      console.error('No se pudieron cargar los datos. La aplicación no continuará.');
      return;
    }
    renderEjecutivo();
    setupFilters('top3', updateTop3Filters);
    setupFilters('radar', renderRadarIndependiente);
    setupFilters('preguntas', renderPreguntas);
    setupFilters('detalle', renderDetalleCarreras);
    setupFilters('visibilidad', renderVisibilidad);
    setupProgressBar();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

window.addEventListener('load', () => {
  setTimeout(() => {
    document.getElementById('splash').classList.add('fade-out');
    document.getElementById('main-wrapper').classList.add('visible');
    setTimeout(() => document.getElementById('splash').remove(), 800);
  }, 1500);
});
