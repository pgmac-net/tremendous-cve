{{- define "tremendous-cve.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "tremendous-cve.fullname" -}}
{{- default .Chart.Name .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "tremendous-cve.labels" -}}
app.kubernetes.io/name: {{ include "tremendous-cve.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "tremendous-cve.selectorLabels" -}}
app.kubernetes.io/name: {{ include "tremendous-cve.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
