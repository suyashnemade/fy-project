import TitleBar from '../components/TitleBar';

/**
 * Layout — top-level shell.
 *
 * Renders:  [ Sidebar | Main ]
 *
 * `sidebar` is a render-prop so the parent can pass any sidebar component.
 * `children` fills the main column (TopBar → content → Footer).
 */
export default function Layout({ sidebar, children }) {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background text-foreground">
      {/* Our Custom Frameless Titlebar */}
      <TitleBar />
      
      {/* The rest of the App */}
      <div className="flex flex-1 overflow-hidden" style={{ height: 'calc(100vh - 2.5rem)' }}>
        {sidebar}
        <div className="flex-1 flex flex-col overflow-y-auto w-full h-full">
          {children}
        </div>
      </div>
    </div>
  );
}
