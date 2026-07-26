export function BomEditor({ productId }: { productId: string }) {
  const [lines, setLines] = useState<BomLine[]>([]);
  const [allItems, setAllItems] = useState<Item[]>([]);

  useEffect(() => {
    api<BomLine[]>(`/boms?product_item_id=${productId}`).then(setLines);
    api<Item[]>('/items?is_product=0').then(setAllItems);
  }, [productId]);

  const save = async () => {
    try {
      await api('/boms/create', {
        method: 'POST',
        body: JSON.stringify({
          product_item_id: productId,
          components: lines.map(l => ({ component_item_id: l.item_id, quantity: l.quantity })),
        }),
      });
      haptic.success();
      tg.showAlert('Спецификация сохранена');
    } catch (e: any) { tg.showAlert(e.message); }
  };

  return (
    <div>
      {lines.map((l, i) => (
        <div className="bom-row" key={i}>
          <ItemPicker items={allItems} value={l.item_id}
                      onChange={id => update(i, { item_id: id })} />
          <input type="number" min={1} value={l.quantity}
                 onChange={e => update(i, { quantity: +e.target.value })} />
          <button onClick={() => remove(i)}>🗑</button>
        </div>
      ))}
      <button onClick={() => setLines([...lines, { item_id: '', quantity: 1 }])}>+ Компонент</button>
      <button className="big-btn primary" onClick={save}>💾 Сохранить BOM</button>
    </div>
  );
}