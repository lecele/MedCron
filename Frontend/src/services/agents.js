export const processMessage = async ({ messageText, history = [], fileData = null }) => {
  try {
    const apiUrl = '/api/chat';

    let usuarioId = localStorage.getItem('med_temp_uid');
    if (!usuarioId || usuarioId.startsWith('web_')) {
      usuarioId = crypto.randomUUID();
      localStorage.setItem('med_temp_uid', usuarioId);
    }
    const sessaoId = localStorage.getItem('med_sessao_id') || null;

    let base64Image = null;
    if (fileData) {
      base64Image = fileData;
    }

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json' 
      },
      body: JSON.stringify({
        message: messageText || "",
        image_base64: base64Image,
        usuario_id: usuarioId,
        sessao_id: sessaoId,
        history: history,
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erro na API: ${response.status}`);
    }

    const data = await response.json();

    // Persiste o sessao_id retornado pelo backend para manter contexto entre mensagens
    if (data.sessao_id) {
      localStorage.setItem('med_sessao_id', data.sessao_id);
    }

    // Retorna a resposta como string com metadado de medicamentos salvos anexado
    // O _medsCount é uma propriedade oculta para o App.jsx saber que listas devem ser recarregadas
    const resposta = data.resposta || '';
    const medsCount = data.medicamentos_salvos || 0;

    // Técnica: criar um objeto String com propriedade extra para passar para o App.jsx
    // sem quebrar a lógica existente que espera uma string
    const result = new String(resposta);
    result._medsCount = medsCount;
    result._alertas = data.alertas_clinicos || [];
    return result;

  } catch (e) {
    console.error("[MedCron HTTP Proxy] Erro:", e);
    throw e;
  }
};
