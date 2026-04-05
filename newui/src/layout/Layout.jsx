import '../styles/layout.css';

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
    <div className="layout">
      {sidebar}
      <div className="layout__main">
        {children}
      </div>
    </div>
  );
}
