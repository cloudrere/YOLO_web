<template>
  <AppLayout>
    <section class="workstation-hero">
      <div>
        <span class="eyebrow dark">智能问答模块</span>
        <h2>AI 深度学习助手</h2>
        <p>接入 DeepSeek 或 OpenAI 兼容接口的独立问答助手，帮助解释检测结果、排查问题、整理优化思路。</p>
      </div>
      <el-tag :type="status?.configured ? 'success' : 'warning'" size="large">{{ status?.configured ? `已配置：${status.model}` : '未配置 API Key' }}</el-tag>
    </section>

    <section class="assistant-workspace">
      <aside class="workstation-panel" style="padding: 0;">
        <div class="assistant-tool-panel">
          <h3>快捷提问</h3>
          <p>选择常用提示词快速开始</p>
          <el-button v-for="item in prompts" :key="item" text @click="question = item" style="display: block; width: 100%; margin-bottom: 4px; text-align: left; font-size: 13px;">{{ item }}</el-button>
          <div class="assistant-status-box">
            <span>服务状态</span>
            <strong>{{ status?.configured ? '可用' : '未配置' }}</strong>
            <small>{{ status?.model || '等待配置 AI_ASSISTANT_API_KEY' }}</small>
          </div>
        </div>
      </aside>

      <main class="workstation-panel" style="padding: 0;">
        <div class="assistant-chat-panel">
          <div class="assistant-conversation">
            <div class="chat-bubble assistant">
              <strong>AI 深度学习助手</strong>
              <p>我可以帮助解释 YOLO 检测结果、排查 GPU/CUDA 问题、整理模型管理和深度学习训练分析思路。</p>
            </div>
            <template v-for="message in messages" :key="message.id">
              <div class="chat-bubble user"><strong>你</strong><p>{{ message.question }}</p></div>
              <div class="chat-bubble assistant"><strong>AI 助手</strong><p>{{ message.answer }}</p></div>
            </template>
            <el-empty v-if="!messages.length" :description="status?.configured ? '发送问题后显示对话' : '后端未配置 AI_ASSISTANT_API_KEY'" style="margin-top: 40px;" />
          </div>
          <div class="assistant-input-bar">
            <el-input v-model="question" type="textarea" :rows="3" placeholder="请输入你的问题，例如：如何解释这批检测结果？" @keyup.ctrl.enter="send" />
            <div class="form-actions" style="margin-top: 10px;">
              <el-button size="small" @click="question = ''">清空</el-button>
              <el-button type="primary" size="small" :loading="loading" :disabled="!question.trim() || !status?.configured" @click="send">发送问题</el-button>
            </div>
          </div>
        </div>
      </main>
    </section>
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
  try {
    const data = await askAssistant(text)
    messages.value.push({ id: Date.now(), question: text, answer: data.answer })
    status.value = { configured: data.configured, model: data.model }
    question.value = ''
  } finally { loading.value = false }
}
onMounted(loadStatus)
</script>
