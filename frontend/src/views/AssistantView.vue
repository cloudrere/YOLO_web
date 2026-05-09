<template>
  <AppLayout>
    <el-card shadow="never" class="mb-s">
      <template #header>
        <div class="flex-between">
          <span>AI深度学习助手</span>
          <el-tag size="small" :type="status?.configured ? 'success' : 'warning'">{{ status?.configured ? `已配置：${status.model}` : '未配置 API Key' }}</el-tag>
        </div>
      </template>
      <p>可接入 DeepSeek 或 OpenAI 兼容接口，用于说明检测结果、整理排查思路或回答系统使用问题。</p>
    </el-card>

    <div class="ops-chat">
      <el-card shadow="never">
        <template #header>工具区</template>
        <p class="text-muted mb">选择常用提示词快速开始，也可以直接在输入区提问。</p>
        <div class="flex-gap" style="flex-direction:column">
          <el-button v-for="item in prompts" :key="item" text @click="question = item">{{ item }}</el-button>
        </div>
        <el-divider />
        <div class="ops-info-item">
          <span>服务状态</span>
          <strong>{{ status?.configured ? '可用' : '未配置' }}</strong>
          <span>{{ status?.model || '等待配置 AI_ASSISTANT_API_KEY' }}</span>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>对话区</template>
        <div class="ops-chat-msgs">
          <div class="ops-chat-msg assistant"><strong>AI深度学习助手</strong>我可以帮助解释检测结果、排查 GPU/CUDA、整理模型管理和深度学习训练分析问题。</div>
          <template v-for="message in messages" :key="message.id">
            <div class="ops-chat-msg user"><strong>你</strong>{{ message.question }}</div>
            <div class="ops-chat-msg assistant"><strong>AI 助手</strong>{{ message.answer }}</div>
          </template>
          <el-empty v-if="!messages.length" :description="status?.configured ? '发送问题后显示对话记录' : '后端未配置 AI_ASSISTANT_API_KEY'" />
        </div>
        <div class="ops-chat-input">
          <el-input v-model="question" type="textarea" :rows="3" placeholder="请输入你的问题，Ctrl+Enter 发送" @keyup.ctrl.enter="send" />
          <div class="flex-gap" style="flex-shrink:0">
            <el-button @click="question = ''">清空</el-button>
            <el-button type="primary" :loading="loading" :disabled="!question.trim() || !status?.configured" @click="send">发送</el-button>
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
  const text = question.value.trim()
  if (!text) return
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
