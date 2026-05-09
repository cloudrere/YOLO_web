<template>
  <AppLayout>
    <div class="bi-page-header">
      <div>
        <h2>AI深度学习助手</h2>
        <p>可接入 DeepSeek 或 OpenAI 兼容接口，用于分析检测结果、排查问题或回答系统使用问题。</p>
      </div>
      <el-tag :type="status?.configured ? 'success' : 'warning'" size="small">{{ status?.configured ? `已配置：${status.model}` : '未配置 API Key' }}</el-tag>
    </div>

    <div class="bi-assistant-grid">
      <el-card shadow="never" class="bi-panel-card">
        <template #header><span class="bi-card-title">推荐问题</span></template>
        <div class="bi-prompt-list">
          <el-button v-for="item in prompts" :key="item" text @click="question = item" class="bi-prompt-btn">{{ item }}</el-button>
        </div>
        <div class="bi-assistant-status-box">
          <div class="bi-status-dot" :style="{ background: status?.configured ? 'var(--color-success)' : 'var(--color-gray-400)' }"></div>
          <div>
            <strong>{{ status?.configured ? '可用' : '未配置' }}</strong>
            <small>{{ status?.model || '等待配置 AI_ASSISTANT_API_KEY' }}</small>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="bi-panel-card bi-chat-panel">
        <div class="bi-chat-conversation">
          <div class="bi-chat-msg assistant">
            <strong>AI深度学习助手</strong>
            <p>我可以帮助解释检测结果、排查 GPU/CUDA、整理模型管理和深度学习训练分析问题。</p>
          </div>
          <template v-for="message in messages" :key="message.id">
            <div class="bi-chat-msg user"><strong>你</strong><p>{{ message.question }}</p></div>
            <div class="bi-chat-msg assistant"><strong>AI 助手</strong><p>{{ message.answer }}</p></div>
          </template>
          <el-empty v-if="!messages.length" :description="status?.configured ? '发送问题后显示对话记录' : '后端未配置 AI_ASSISTANT_API_KEY，配置后即可使用'" :image-size="60" />
        </div>
        <div class="bi-chat-input-bar">
          <el-input v-model="question" type="textarea" :rows="3" placeholder="请输入你的问题…" @keyup.ctrl.enter="send" />
          <div class="bi-chat-actions">
            <el-button size="small" @click="question = ''">清空输入</el-button>
            <el-button type="primary" size="small" :loading="loading" :disabled="!question.trim() || !status?.configured" @click="send">发送问题</el-button>
          </div>
        </div>
      </el-card>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import { askAssistant, getAssistantStatus, type AssistantStatus } from '@/api/assistant'

const status = ref<AssistantStatus | null>(null)
const question = ref('')
const loading = ref(false)
const messages = ref<Array<{ id: number; question: string; answer: string }>>([])
const prompts = ['如何排查 GPU 无法使用？', '如何解释检测结果中的低置信度？', '如何给新模型维护中文类别？']

async function loadStatus() { status.value = await getAssistantStatus() }
async function send() {
  const text = question.value.trim(); if (!text) return
  loading.value = true
  try { const data = await askAssistant(text); messages.value.push({ id: Date.now(), question: text, answer: data.answer }); status.value = { configured: data.configured, model: data.model }; question.value = '' }
  finally { loading.value = false }
}
onMounted(loadStatus)
</script>
