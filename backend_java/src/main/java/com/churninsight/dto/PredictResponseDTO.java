package com.churninsight.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class PredictResponseDTO {

    @JsonProperty("previsao")
    private String previsao;

    @JsonProperty("probabilidade")
    private Double probabilidade;

    public PredictResponseDTO() {}

    public PredictResponseDTO(String previsao, Double probabilidade) {
        this.previsao = previsao;
        this.probabilidade = probabilidade;
    }

    public String getPrevisao() { return previsao; }
    public void setPrevisao(String previsao) { this.previsao = previsao; }

    public Double getProbabilidade() { return probabilidade; }
    public void setProbabilidade(Double probabilidade) { this.probabilidade = probabilidade; }
}