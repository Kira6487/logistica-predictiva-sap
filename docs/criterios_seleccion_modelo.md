# Criterios de selección del modelo

## Métricas

- **MAE:** error absoluto medio en unidades.
- **RMSE:** penaliza errores grandes.
- **WAPE:** error absoluto total dividido entre demanda real total.
- **sMAPE:** error porcentual simétrico.
- **Bias:** promedio de predicción menos demanda real.

## Selección

1. Se descartan ajustes con error técnico.
2. Se selecciona el menor WAPE.
3. MAE funciona como desempate.
4. Si la demanda real del test es cero y WAPE no puede calcularse, se utiliza
   MAE y después RMSE.

## Confianza

- `HIGH`: WAPE hasta 20%, seis meses evaluados y serie no intermitente.
- `MEDIUM`: WAPE hasta 50%.
- `LOW`: WAPE superior a 50%, WAPE no calculable o serie irregular.
- `NOT_RECOMMENDED`: ningún modelo pudo evaluarse.

Resultado real:

- Alta: 0.
- Media: 18.
- Baja: 155.
- No recomendada por fallo técnico: 0.

## Intervalos

Los límites futuro inferior y superior son aproximaciones construidas con
`forecast ± 1.96 × RMSE` del modelo ganador. El límite inferior nunca es menor
que cero. No son intervalos probabilísticos calibrados y deben presentarse como
bandas de incertidumbre operativa.

## Paso a reposición

La reposición puede implementarse como siguiente capa técnica, pero debe:

1. comenzar con los artículos de confianza media;
2. conservar revisión humana;
3. añadir stock, comprometido, en camino, lead time y seguridad;
4. impedir cantidades de compra negativas;
5. mostrar confianza y error junto con cada recomendación.
