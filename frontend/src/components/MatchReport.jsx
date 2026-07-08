const SECTION_LABELS = {
  content: 'Nội dung',
  skills: 'Kỹ năng',
  format: 'Định dạng',
  profile: 'Hồ sơ',
  style: 'Phong cách',
}

const ORDER = ['content', 'skills', 'format', 'profile', 'style']

function pct(value) { return Math.round(Number(value || 0)) }
function countIssues(section) { return Number(section?.suggestion_count || 0) }
function scoreClass(score) { return score >= 75 ? 'match-good' : score >= 55 ? 'match-mid' : 'match-low' }

function SectionNav({ sections }) {
  return <div className="match-nav">{ORDER.map(key => {
    const section = sections?.[key] || {}
    const issues = countIssues(section)
    return <a key={key} href={`#match-${key}`} className={issues ? '' : 'complete'}>
      <span>{section.title || SECTION_LABELS[key]}</span>
      <small>{issues ? `${issues} đề xuất` : 'ĐẠT'}</small>
    </a>
  })}</div>
}

function SkillTable({ items = [] }) {
  if (!items.length) return <p className="muted">Không có kỹ năng để so sánh.</p>
  return <div className="skill-table"><table><thead><tr><th>Kỹ năng</th><th>Loại</th><th>JD</th><th>CV</th><th>Trạng thái</th></tr></thead><tbody>{items.map(item => <tr key={`${item.skill}-${item.kind}`}>
    <td><b>{item.skill}</b></td>
    <td>{item.required ? 'Bắt buộc' : 'Ưu tiên'}</td>
    <td>{item.jd_count}</td>
    <td>{item.cv_count}</td>
    <td><span className={'badge '+(item.status === 'matched' ? 'badge-success' : 'badge-danger')}>{item.status === 'matched' ? 'Khớp' : 'Thiếu'}</span></td>
  </tr>)}</tbody></table></div>
}

function SectionBody({ id, section }) {
  const items = section?.items || []
  return <article id={`match-${id}`} className="match-section card">
    <div className="section-title"><div><h2>{section?.title || SECTION_LABELS[id]}</h2><p className="muted">{section?.description}</p></div><span className={'badge '+(countIssues(section) ? 'badge-warning' : 'badge-success')}>{section?.badge || 'ĐẠT'}</span></div>
    {id === 'skills' ? <SkillTable items={items} /> : items.length ? <ul>{items.map((item, index) => <li key={item.skill || item.label || item.text || index}>{item.message || item.text || item.label || item.skill}</li>)}</ul> : <p className="muted">Không có đề xuất mới.</p>}
  </article>
}

export default function MatchReport({ match, jobTitle, companyName, onClose }) {
  if (!match) return null
  const score = pct(match.overall_score)
  const sections = match.sections || {}
  const totalIssues = ORDER.reduce((sum, key) => sum + countIssues(sections[key]), 0)
  const report = <div className="match-report">
    <div className="match-sidebar">
      <div className="match-steps"><span>Bước 1<br/><b>Phân tích</b></span><span>Bước 2<br/><b>CV</b></span><span>Bước 3<br/><b>JD</b></span></div>
      <h2>{jobTitle || match.job_title || 'CV/JD Matching'}</h2>
      {companyName && <p className="muted">{companyName}</p>}
      <div className={'score-ring '+scoreClass(score)} style={{'--score': `${score * 3.6}deg`}}><span>{score}</span></div>
      <p><b>{totalIssues}</b> đề xuất</p>
      <p className="muted">CV trên 75 điểm thường có khả năng vượt qua bước lọc tốt hơn.</p>
      <SectionNav sections={sections} />
    </div>
    <div className="match-main">
      <div className="match-actions">{onClose && <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>Đóng report</button>}</div>
      <section className="match-overview card">
        <h1>Tổng quan</h1>
        <p><b>Mức độ phù hợp: {score}</b></p>
        <p>{match.fit_summary || 'Chưa có phân tích chi tiết.'}</p>
        <div className="overview-grid">
          <div className="good-box"><h3>Điểm nổi bật</h3><ul>{(match.strengths || []).map(x => <li key={x}>{x}</li>)}</ul></div>
          <div className="warn-box"><h3>Cải thiện</h3><ul>{(match.improvements || []).map(x => <li key={x}>{x}</li>)}</ul></div>
        </div>
      </section>
      {ORDER.map(key => <SectionBody key={key} id={key} section={sections[key]} />)}
    </div>
  </div>
  if (!onClose) return report
  return <div className="report-modal" role="dialog" aria-modal="true">
    <button type="button" className="report-backdrop" aria-label="Close report" onClick={onClose} />
    <div className="report-modal-body">{report}</div>
  </div>
}
