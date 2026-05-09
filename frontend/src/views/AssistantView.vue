<template>
  <AppLayout>
    <div class="ws-page-header">
      <div>
        <h1>AI 深度学习助手</h1>
        <p>接入 DeepSeek 或 OpenAI 兼容接口，解释检测结果、排查 GPU/CUDA、整理模型管理问题。</p>
      </div>
      <el-tag size="small" :type="status?.configured ? 'success' : 'warning'">{{ status?.configured ? `已配置：${status.model}` : '未配置 API Key' }}</el-tag>
    </div>

    <div class="ws-chat">
      <div class="ws-card">
        <div class="ws-card-header">工具区</div>
        <div class="ws-card-body">
          <p class="text-muted mb">选择常用提示词快速开始</p>
          <div class="flex-gap" style="flex-direction:column">
            <el-button v-for="item in prompts" :key="item" text @click="question = item" style="justify-content:flex-start;text-align:left">{{ item }}</el-button>
          </div>
          <el-divider />
          <div class="ws-info-item">
            <span class="info-label">服务状态</span>
            <span class="info-value">{{ status?.configured ? '可用' : '未配置' }}</span>
          </div>
        </div>
      </div>

      <div class="ws-card">
        <div class="ws-card-header">对话区</div>
        <div class="ws-card-body">
          <div class="ws-chat-msgs">
            <div class="ws-chat-msg assistant"><strong>AI 助手</strong>我可以帮助解释检测结果、排查 GPU/CUDA、整理模型管理和深度学习训练分析问题。</div>
            <template v-for="msg in messages" :key="msg.id">
              <div class="ws-chat-msg user"><strong>你</strong>{{ msg.question }}</div>
              <div class="ws-chat-msg assistant"><strong>AI 助手</strong>{{ msg.answer }}</div>
            </template>
            <el-empty v-if="!messages.length" :description="status?.configured ? '发送问题后显示对话' : '后端未配置 AI_ASSISTANT_API_KEY'" />
          </div>
          <div style="display:flex;gap:8px;align-items:flex-end;margin-top:10px">
            <el-input v-model="question" type="textarea" :rows="3" placeholder="请输入问题，Ctrl+Enter 发送" @keyup.ctrl.enter="send" style="flex:1" />
            <div style="display:flex;gap:6px;flex-shrink:0">
              <el-button @click="question = ''">清空</el-button>
              <el-button type="primary" :loading="loading" :disabled="!question.trim() || !status?.configured" @click="send">发送</el-button>
            </div>
          </div>
        </div>
      </div>
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
