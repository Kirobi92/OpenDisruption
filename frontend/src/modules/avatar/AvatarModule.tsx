import { useCallback } from 'react'
import { useAgentWebSocket } from '../../hooks/useAgentWebSocket'
import { KirobiAvatar } from '../../components/avatar/KirobiAvatar'
import { StatusBar } from '../../components/ui/StatusBar'
import { TranscriptPanel } from '../../components/ui/TranscriptPanel'
import { MicButton } from '../../components/ui/MicButton'
import { BackendSwitcher } from '../../components/ui/BackendSwitcher'

export default function AvatarModule() {
  const { sendInterrupt, unlockAudio } = useAgentWebSocket()

  const handleUnlock = useCallback(() => {
    void unlockAudio()
  }, [unlockAudio])

  return (
    <section className="avatarModule" onPointerDown={handleUnlock}>
      <StatusBar />
      <BackendSwitcher />
      <main className="main avatarMain">
        <div className="avatarArea">
          <KirobiAvatar />
          <div className="avatarGlow" />
        </div>
        <div className="titleArea">
          <h1 className="title">KIROBI</h1>
          <p className="subtitle">Avatar Agent · Voice Core</p>
        </div>
      </main>
      <footer className="footer avatarFooter">
        <TranscriptPanel />
        <MicButton onInterrupt={sendInterrupt} />
      </footer>
    </section>
  )
}
