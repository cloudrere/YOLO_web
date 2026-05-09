<template>
  <AppLayout>
    <div class="page-header">
      <div>
        <h2>AI 助手</h2>
        <p>接入 DeepSeek 或 OpenAI 兼容接口，用于分析检测结果与排查问题</p>
      </div>
      <el-tag :type="status?.configured ? 'success' : 'warning'" size="small">{{ status?.configured ? `已配置：${status.model}` : '未配置 API Key' }}</el-tag>
    </div>

    <div class="chat-layout">
      <div class="chat-sidebar">
        <el-card shadow="never">
          <template #header>推荐问题</template>
          <div style="display:flex;flex-direction:column;gap:6px">
            <el-button v-for="item in prompts" :key="item" text @click="question = item" style="justify-content:flex-start;text-align:left;font-size:13px">{{ item }}</el-button>
          </div>
        </el-card>
        <div style="display:flex;align-items:center;gap:10px;padding:12px;border:1px solid #e4e7ed;border-radius:4px;background:#fff">
          <div style="width:8px;height:8px;border-radius:4px" :style="{ background: status?.configured ? '#67c23a' : '#c0c4cc' }"></div>
          <div>
            <strong style="font-size:13px;display:block">{{ status?.configured ? '可用' : '未配置' }}</strong>
            <small style="font-size:11px;color:#909399">{{ status?.model || '等待配置 AI_ASSISTANT_API_KEY' }}</small>
          </div>
        </div>
      </div>

      <el-card shadow="never" class="chat-main" style="display:flex;flex-direction:column">
        <div class="chat-messages">
          <div class="chat-msg assistant">
            <strong>AI 助手</strong>
            <p style="color:#303133">我可以帮助解释检测结果、排查 GPU/CUDA、整理模型管理和深度学习训练分析问题。</p>
          </div>
          <template v-for="message in messages" :key="message.id">
            <div class="chat-msg user"><strong>你</strong><p style="color:#fff">{{ message.question }}</p></div>
            <div class="chat-msg assistant"><strong>AI 助手</strong><p style="color:#303133">{{ message.answer }}</p></div>
          </template>
          <el-empty v-if="!messages.length" :description="status?.configured ? '发送问题后显示对话记录' : '后端未配置 AI_ASSISTANT_API_KEY，配置后即可使用'" :image-size="48" />
        </div>
        <div class="chat-input-bar">
          <el-input v-model="question" type="textarea" :rows="3" placeholder="请输入你的问题…" @keyup.ctrl.enter="send" />
          <div style="display:flex;flex-direction:column;gap:6px">
            <el-button size="small" @click="question = ''">清空</el-button>
            <el-button type="primary" size="small" :loading="loading" :disabled="!question.trim() || !status?.configured" @click="send">发送</el-button>
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
